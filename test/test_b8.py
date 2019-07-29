#!/usr/bin/env python3

import unittest
import subprocess

import b8


class TestB8(unittest.TestCase):

    def test_main(self):
        b8_path = b8.__file__
        document_url = 'https://max.book118.com/html/2019/0127/6202200032002004.shtm'
        result = subprocess.run(['python3', b8_path, document_url], check=True)
        self.assertEqual(result.returncode, 0)

    def test_get_url_params(self):
        urls_params = {
            r'https://fanyi.baidu.com/?aldtype=85#en/zh/hello': {'aldtype': '85'},
            r'https://github.com/audreyr/cookiecutter-pypackage#support-this-project': {},
            r'https://www.baidu.com/s?wd=2020%E5%A4%AE%E8%A7%86%E6%98%A5%E6%99%9A&usm=1&ie=utf-8':
            {'wd': '2020央视春晚', 'usm': '1', 'ie': 'utf-8'}
        }
        for url, params in urls_params.items():
            self.assertEqual(b8.get_url_params(url), params)

    def test_update_url_params(self):
        urls_params = {
            r'https://fanyi.baidu.com/?aldtype=85#en/zh/hello':
            ({'aldtype': 99}, {'aldtype': '99'}),
            r'https://github.com/audreyr/cookiecutter-pypackage#support-this-project':
            ({'name': 'mike'}, {'name': 'mike'}),
            r'https://www.baidu.com/s?wd=2020%E5%A4%AE%E8%A7%86%E6%98%A5%E6%99%9A&usm=1&ie=utf-8':
            ({'usm': 'aa'}, {'wd': '2020央视春晚', 'usm': 'aa', 'ie': 'utf-8'})
        }
        for url, params in urls_params.items():
            new_url = b8.update_url_params(url, params[0])
            new_params = b8.get_url_params(new_url)
            self.assertEqual(new_params, params[1])


if __name__ == '__main__':
    unittest.main()
