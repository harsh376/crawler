# Copyright (C) 2011 by Peter Goodman
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os
import urllib2
import urlparse
from BeautifulSoup import *
from collections import defaultdict
import re
import sqlite3
from pagerank import get_page_rank_scores


def attr(elem, attr):
    """An html attribute from an html element. E.g. <a href="">, then
    attr(elem, "href") will get the href or an empty string."""
    try:
        return elem[attr]
    except:
        return ""


WORD_SEPARATORS = re.compile(r'\s|\n|\r|\t|[^a-zA-Z0-9\-_]')
TAGS_TO_COMBINE = 40


class crawler(object):
    """Represents 'Googlebot'. Populates a database by crawling and indexing
    a subset of the Internet.

    This crawler keeps track of font sizes and makes it simpler to manage word
    ids and document ids."""

    def __init__(self, db_conn, url_file):
        """
        Initialize the crawler with a connection to the database to populate
        and with the file containing the list of seed URLs to begin indexing.
        """
        self._url_queue = []
        # self._doc_id_cache = {}
        # self._word_id_cache = {}
        # self._inverted_index = {}   # {word_id1: [doc_id1, doc_id2, ...]}

        # initialize database
        self.db_conn = db_conn
        self.cursor = self.db_conn.cursor()
        # TODO: Update executescript to initialize required tables
        self.cursor.executescript(
            """
            DROP TABLE IF EXISTS lexicon;
            DROP TABLE IF EXISTS doc_index;
            DROP TABLE IF EXISTS inverted_index;
            DROP TABLE IF EXISTS links;
            DROP TABLE IF EXISTS page_ranks;
            DROP TABLE IF EXISTS snippets;

            CREATE TABLE IF NOT EXISTS
                lexicon(id INTEGER PRIMARY KEY, word TEXT UNIQUE);
            CREATE TABLE IF NOT EXISTS
                doc_index(
                    id INTEGER PRIMARY KEY,
                    url TEXT UNIQUE,
                    title TEXT
                );
            CREATE TABLE IF NOT EXISTS
                inverted_index(
                    word_id INTEGER,
                    doc_id INTEGER,
                    snippet_id INTEGER,
                    UNIQUE(word_id, doc_id, snippet_id)
                );
            CREATE TABLE IF NOT EXISTS
                snippets(id INTEGER PRIMARY KEY, text TEXT UNIQUE);
            CREATE TABLE IF NOT EXISTS
                links(from_doc_id INTEGER, to_doc_id INTEGER);
            CREATE TABLE IF NOT EXISTS
                page_ranks(doc_id INTEGER PRIMARY KEY, rank REAL);
            """
        )

        # functions to call when entering and exiting specific tags
        self._enter = defaultdict(lambda *a, **ka: self._visit_ignore)
        self._exit = defaultdict(lambda *a, **ka: self._visit_ignore)

        # add a link to our graph, and indexing info to the related page
        self._enter['a'] = self._visit_a

        # record the currently indexed document's title an increase
        # the font size
        def visit_title(*args, **kargs):
            self._visit_title(*args, **kargs)
            self._increase_font_factor(7)(*args, **kargs)

        # increase the font size when we enter these tags
        self._enter['b'] = self._increase_font_factor(2)
        self._enter['strong'] = self._increase_font_factor(2)
        self._enter['i'] = self._increase_font_factor(1)
        self._enter['em'] = self._increase_font_factor(1)
        self._enter['h1'] = self._increase_font_factor(7)
        self._enter['h2'] = self._increase_font_factor(6)
        self._enter['h3'] = self._increase_font_factor(5)
        self._enter['h4'] = self._increase_font_factor(4)
        self._enter['h5'] = self._increase_font_factor(3)
        self._enter['title'] = visit_title

        # decrease the font size when we exit these tags
        self._exit['b'] = self._increase_font_factor(-2)
        self._exit['strong'] = self._increase_font_factor(-2)
        self._exit['i'] = self._increase_font_factor(-1)
        self._exit['em'] = self._increase_font_factor(-1)
        self._exit['h1'] = self._increase_font_factor(-7)
        self._exit['h2'] = self._increase_font_factor(-6)
        self._exit['h3'] = self._increase_font_factor(-5)
        self._exit['h4'] = self._increase_font_factor(-4)
        self._exit['h5'] = self._increase_font_factor(-3)
        self._exit['title'] = self._increase_font_factor(-7)

        # never go in and parse these tags
        self._ignored_tags = set([
            'meta', 'script', 'link', 'meta', 'embed', 'iframe', 'frame',
            'noscript', 'object', 'svg', 'canvas', 'applet', 'frameset',
            'textarea', 'style', 'area', 'map', 'base', 'basefont', 'param',
        ])

        # set of words to ignore
        self._ignored_words = set([
            '', 'the', 'of', 'at', 'on', 'in', 'is', 'it',
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
            'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
            'u', 'v', 'w', 'x', 'y', 'z', 'and', 'or',
        ])

        # TODO remove me in real version
        self._mock_next_doc_id = 1
        self._mock_next_word_id = 1

        # keep track of some info about the page we are currently parsing
        self._curr_depth = 0
        self._curr_url = ""
        self._curr_doc_id = 0
        self._font_size = 0
        self._curr_words = None

        # get all urls into the queue
        try:
            url_file_path = os.path.join(os.path.dirname(__file__), url_file)
            with open(url_file_path, 'r') as f:
                for line in f:
                    self._url_queue.append(
                        (self._fix_url(line.strip(), ""), 0))
        except IOError:
            pass

    def __del__(self):
        if self.db_conn:
            self.db_conn.commit()
            self.db_conn.close()

    def get_inverted_index(self):
        """
        :returns
            {
                word_id1: set([
                    (docid1, snip1), (docid1, snip2), (docid2, snip1)
                ]),
                word_id2: set([
                    (docid1, snip1), (docid1, snip2), (docid2, snip1)
                ])
            }
        """
        self.cursor.execute('SELECT * FROM inverted_index;')
        results = self.cursor.fetchall()
        inverted_index = {}
        for word_id, doc_id, snippet_id in results:
            if word_id in inverted_index:
                inverted_index[word_id].add((doc_id, snippet_id))
            else:
                inverted_index[word_id] = set([(doc_id, snippet_id)])
        return inverted_index

    def get_resolved_inverted_index(self):
        """
        :returns
            {word1: set([url1, url2, ...], word2: set([urls....])}
        """

        # More efficient to perform the JOINs on db level rather than fetching
        # data and performing the JOINs in code
        self.cursor.execute(
            """
            SELECT
                a.word_id AS word_id,
                a.word AS word,
                a.doc_id AS doc_id,
                b.url AS url
            FROM (
                SELECT
                    lexicon.id AS word_id,
                    lexicon.word AS word,
                    inverted_index.doc_id AS doc_id
                FROM inverted_index
                INNER JOIN lexicon
                ON inverted_index.word_id = lexicon.id
            ) a
            INNER JOIN (
                SELECT *
                FROM doc_index
            ) b
            ON a.doc_id = b.id;
            """
        )
        result = self.cursor.fetchall()
        resolved_index = {}
        for word_id, word, doc_id, url in result:
            if word in resolved_index:
                resolved_index[word].add(url)
            else:
                resolved_index[word] = set([url])
        return resolved_index

    def update_inverted_index(self, word_id, doc_id, snippet_id):
        """
        Adds (word_id, doc_id, snippet_id) entry into inverted_index table
        """
        self.cursor.execute(
            """
            INSERT OR REPLACE INTO inverted_index(word_id, doc_id, snippet_id)
            VALUES(
                ?, ?, ?
            );
            """,
            (word_id, doc_id, snippet_id),
        )
        self.db_conn.commit()

    # TODO remove me in real version
    def _mock_insert_document(self, url):
        """A function that pretends to insert a url into a document db table
        and then returns that newly inserted document's id."""
        ret_id = self._mock_next_doc_id
        self._mock_next_doc_id += 1
        return ret_id

    # TODO remove me in real version
    def _mock_insert_word(self, word):
        """A function that pretends to inster a word into the lexicon db table
        and then returns that newly inserted word's id."""
        ret_id = self._mock_next_word_id
        self._mock_next_word_id += 1
        return ret_id

    def insert_word_in_lexicon(self, word):
        try:
            self.cursor.execute(
                'INSERT INTO lexicon(word) VALUES(?)',
                (word,),
            )
            self.db_conn.commit()
            word_id = self.cursor.lastrowid
        except sqlite3.Error:
            self.cursor.execute(
                'SELECT * FROM lexicon WHERE word=?',
                (word,),
            )
            entry = self.cursor.fetchone()
            word_id = entry[0]
        return word_id

    def insert_doc_in_doc_index(self, url):
        try:
            self.cursor.execute(
                'INSERT INTO doc_index(url) VALUES(?)',
                (url,),
            )
            self.db_conn.commit()
            doc_id = self.cursor.lastrowid
        except sqlite3.Error:
            self.cursor.execute(
                'SELECT * FROM doc_index WHERE url=?',
                (url,),
            )
            entry = self.cursor.fetchone()
            doc_id = entry[0]
        return doc_id

    def insert_snippet_in_snippets(self, text):
        try:
            self.cursor.execute(
                'INSERT INTO snippets(text) VALUES(?)',
                (text,),
            )
            self.db_conn.commit()
            snippet_id = self.cursor.lastrowid
        except sqlite3.Error:
            self.cursor.execute(
                'SELECT * FROM snippets WHERE text=?',
                (text,),
            )
            entry = self.cursor.fetchone()
            snippet_id = entry[0]
        return snippet_id

    def update_snippet_in_snippets(self, snippet_id, text):
        try:
            self.cursor.execute(
                'UPDATE snippets SET text=? WHERE id=?',
                (text, snippet_id),
            )
            self.db_conn.commit()
        except sqlite3.Error:
            print 'error in update snippet'

    def get_snippets(self):
        self.cursor.execute('SELECT * FROM snippets;')
        results = self.cursor.fetchall()
        snippets = {}
        for snippet_id, text in results:
            snippets[snippet_id] = text
        return snippets

    def word_id(self, word, snippet_id):
        # TODO: add caching
        # insert word in the lexicon
        word_id = self.insert_word_in_lexicon(word=word)

        # insert or update inverted_index with word_id, doc_id, snippet_id
        self.update_inverted_index(
            word_id=word_id,
            doc_id=self._curr_doc_id,
            snippet_id=snippet_id,
        )
        return word_id

    def document_id(self, url):
        # TODO: add caching
        doc_id = self.insert_doc_in_doc_index(url)
        return doc_id

    def _fix_url(self, curr_url, rel):
        """Given a url and either something relative to that url or another url,
        get a properly parsed url."""

        rel_l = rel.lower()
        if rel_l.startswith("http://") or rel_l.startswith("https://"):
            curr_url, rel = rel, ""

        # compute the new url based on import
        curr_url = urlparse.urldefrag(curr_url)[0]
        parsed_url = urlparse.urlparse(curr_url)
        return urlparse.urljoin(parsed_url.geturl(), rel)

    def add_link(self, from_doc_id, to_doc_id):
        """
        Add a link into the database, or increase the number of links
        between two pages in the database.
        """
        # print (from_doc_id, to_doc_id)
        if self.db_conn:
            self.cursor.execute(
                'INSERT INTO links VALUES (?, ?)',
                (from_doc_id, to_doc_id),
            )
            self.db_conn.commit()

    def update_title(self, doc_id, title_text):
        self.cursor.execute(
            'UPDATE doc_index SET title=? WHERE id=?',
            (title_text, doc_id),
        )
        self.db_conn.commit()

    def _visit_title(self, elem):
        """Called when visiting the <title> tag."""
        title_text = self._text_of(elem).strip()
        doc_title = title_text.encode('utf-8')
        self.update_title(doc_id=self._curr_doc_id, title_text=doc_title)

    def _visit_a(self, elem):
        """Called when visiting <a> tags."""

        dest_url = self._fix_url(self._curr_url, attr(elem, "href"))

        # print "href="+repr(dest_url), \
        #      "title="+repr(attr(elem,"title")), \
        #      "alt="+repr(attr(elem,"alt")), \
        #      "text="+repr(self._text_of(elem))

        # add the just found URL to the url queue
        self._url_queue.append((dest_url, self._curr_depth))

        # add a link entry into the database from the current document to the
        # other document
        self.add_link(self._curr_doc_id, self.document_id(dest_url))

        # TODO add title/alt/text to index for destination url

    def _add_words_to_document(self):
        # TODO: knowing self._curr_doc_id and the list of all words and their
        #       font sizes (in self._curr_words), add all the words into the
        #       database for this document
        print "    num words=" + str(len(self._curr_words))

    def _increase_font_factor(self, factor):
        """Increase/decrease the current font size."""

        def increase_it(elem):
            self._font_size += factor

        return increase_it

    def _visit_ignore(self, elem):
        """Ignore visiting this type of tag"""
        pass

    def _add_text(self, snippet):
        """
        Add some text to the document. This records word ids and word font
        sizes into the self._curr_words list for later processing.
        """
        clean_snippet = ''
        words = WORD_SEPARATORS.split(snippet['string'].lower())

        snippet_id = self.insert_snippet_in_snippets('init_snippet_val')

        for word in words:
            word = word.strip()
            clean_snippet = clean_snippet + ' ' + word

            if word in self._ignored_words:
                continue
            self._curr_words.append(
                (self.word_id(word, snippet_id), self._font_size),
            )

        # update snippets table with `clean_snippet`
        self.update_snippet_in_snippets(
            snippet_id=snippet_id,
            text=clean_snippet,
        )

    def _text_of(self, elem):
        """Get the text inside some element without any tags."""
        if isinstance(elem, Tag):
            text = []
            for sub_elem in elem:
                text.append(self._text_of(sub_elem))

            return " ".join(text)
        else:
            return elem.string

    def _index_document(self, soup):
        """
        Traverse the document in depth-first order and call functions when
        entering and leaving tags. When we come accross some text, add it into
        the index. This handles ignoring tags that we have no business looking
        at.
        """
        class DummyTag(object):
            next = False
            name = ''

        class NextTag(object):
            def __init__(self, obj):
                self.next = obj

        tag = soup.html
        stack = [DummyTag(), soup.html]
        snippet = ''
        tag_num = 0

        while tag and tag.next:
            tag = tag.next

            # html tag
            if isinstance(tag, Tag):

                if tag.parent != stack[-1]:
                    self._exit[stack[-1].name.lower()](stack[-1])
                    stack.pop()

                tag_name = tag.name.lower()

                # ignore this tag and everything in it
                if tag_name in self._ignored_tags:
                    if tag.nextSibling:
                        tag = NextTag(tag.nextSibling)
                    else:
                        self._exit[stack[-1].name.lower()](stack[-1])
                        stack.pop()
                        tag = NextTag(tag.parent.nextSibling)

                    continue

                # enter the tag
                self._enter[tag_name](tag)
                stack.append(tag)

            # text (text, cdata, comments, etc.)
            else:
                if tag_num > TAGS_TO_COMBINE:
                    snippet = {'string': snippet}
                    self._add_text(snippet)

                    # set values back to initial values
                    snippet = ''
                    tag_num = 0
                else:
                    snippet += tag
                    tag_num += 1

    def crawl(self, depth=2, timeout=3):
        """Crawl the web!"""
        seen = set()

        while len(self._url_queue):

            url, depth_ = self._url_queue.pop()

            # skip this url; it's too deep
            if depth_ > depth:
                continue

            doc_id = self.document_id(url)

            # we've already seen this document
            if doc_id in seen:
                continue

            seen.add(doc_id)  # mark this document as haven't been visited

            socket = None
            try:
                socket = urllib2.urlopen(url, timeout=timeout)
                soup = BeautifulSoup(socket.read())

                self._curr_depth = depth_ + 1
                self._curr_url = url
                self._curr_doc_id = doc_id
                self._font_size = 0
                self._curr_words = []
                self._index_document(soup)
                self._add_words_to_document()
                print "    url=" + repr(self._curr_url)

            except Exception as e:
                print e
                pass
            finally:
                if socket:
                    socket.close()

    def update_page_ranks(self):
        if self.cursor:
            self.cursor.execute('SELECT * FROM links;')
            links = self.cursor.fetchall()
            page_rank_map = get_page_rank_scores(links=links)
            for doc_id in page_rank_map:
                self.cursor.execute(
                    """
                    INSERT OR REPLACE INTO page_ranks(doc_id, rank) VALUES(
                        ?, ?
                    )
                    """,
                    (doc_id, page_rank_map[doc_id]),
                )
            self.db_conn.commit()

    def get_page_ranks(self):
        if self.cursor:
            self.cursor.execute('SELECT * FROM page_ranks;')
            result = self.cursor.fetchall()
            return result


if __name__ == '__main__':
    db_conn = sqlite3.connect('backend.db')
    bot = crawler(db_conn=db_conn, url_file='urls.txt')
    # Adjust the depth to determine how deep you want the crawler to crawl
    bot.crawl(depth=0)
    bot.update_page_ranks()

    data = bot.get_page_ranks()
    print (data)

