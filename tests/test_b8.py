#!/usr/bin/env python3

import os
import unittest
import subprocess

from .context import b8


class TestB8(unittest.TestCase):

    def test_b8(self):
        b8_path = b8.__file__
        document_url = 'https://max.book118.com/html/2019/0127/6202200032002004.shtm'
        result = subprocess.run(['python3', b8_path, document_url])
        self.assertEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()
