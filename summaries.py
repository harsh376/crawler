import summary

TEST_URL = 'https://ca.sports.yahoo.com'


def get_summary(url):
    res = ''
    s = summary.Summary(url)
    try:
        s.extract()
        res = s.description
    except:
        print ('Error parsing url: ' + url)
    return res


if __name__ == '__main__':
    res = get_summary(TEST_URL)
    print res
