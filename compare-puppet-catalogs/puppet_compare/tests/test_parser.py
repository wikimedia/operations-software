from puppet_compare import parser
import unittest
import os
dirn = os.path.realpath(os.path.dirname(__file__))
diffile = os.path.join(dirn,"fixtures/diff.json")

class TestParser(unittest.TestCase):

    def setUp(self):
        self.parser = parser.DiffParser(diffile, 'testnode')

    def test_diffs_are_loaded(self):
        self.assertEquals(self.parser._diffs['total_resources_in_new'],399)

    def test_run(self):
        res = self.parser.run()
        self.assertEquals(len(res), 2)
        self.assertTrue(res[0][1])
        self.assertEquals(res[1][1],'')
