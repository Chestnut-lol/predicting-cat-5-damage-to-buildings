from email import utils
import unittest
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from data_loading.tif_links_utils import *
from data_loading.vector_data_utils import *

class TestTifLinksUtils(unittest.TestCase):
    def test_get_tif_links(self):
        hurricane_name = "test"
        links = get_raw_tif_links(hurricane_name, False)
        assert len(links) == 5

    def test_tidy_up_tif_links_with_non_existent_tidied_file(self):
        # Arrange
        # Make sure that tidied file list does not exist
        hurricane_name = "test"
        path = os.path.join(PATH_TO_TIDIED_FILELISTS, hurricane_name)
        check_if_file_exist(path, True)
        links = get_raw_tif_links(hurricane_name, False)

        # Act
        res = tidy_up_tif_links(links, hurricane_name, False)

        # Assert
        # Should have only 4 links left
        assert len(res) == 4, f"Expect 4 links but get {len(res)} links instead"
        assert os.path.isfile(path) == True
        os.remove(path)
    
    def test_tidy_up_links_with_existing_tidied_file(self):
        # Arrange
        hurricane_name = "test"

        links = get_raw_tif_links(hurricane_name, False)
        ans = tidy_up_tif_links(links, hurricane_name, False, True)

        # Act
        res = tidy_up_tif_links(links, hurricane_name, False, False)
        
        # Assert
        assert len(res) == 4, f"Expect 4 links but get {len(res)} instead"
        assert len(ans) == 4, f"Expect 4 links but get {len(ans)} instead"
        assert ans == res
        


    def test_make_bounding_box_and_find_useful_links(self):
        links = ['https://opendata.digitalglobe.com/events/hurricane-irma/pre-event/2017-09-05/1020010067564E00/1020010067564E00.tif', 'https://opendata.digitalglobe.com/events/hurricane-irma/pre-event/2017-05-20/103001006B055400/103001006B055400.tif', 'https://opendata.digitalglobe.com/events/hurricane-irma/pre-event/2016-09-08/103001005CD78300/103001005CD78300.tif', 'https://opendata.digitalglobe.com/events/hurricane-irma/pre-event/2016-08-25/103001005B6AEB00/103001005B6AEB00.tif', 'https://opendata.digitalglobe.com/events/hurricane-irma/pre-event/2016-02-07/1040010018601F00/1040010018601F00.tif']
        left = -67.2216
        right = -65.1905
        top = 18.5463
        bottom = 17.8603
        (puertoRicoBox, useful_pre_event_links_puerto_rico, useful_post_event_links_puerto_rico)\
             = make_bounding_box_and_find_useful_links(left, bottom, right, top, links, False)
        assert len(useful_pre_event_links_puerto_rico) == 0, f"{len(useful_pre_event_links_puerto_rico)}"
        assert len(useful_post_event_links_puerto_rico) == 0, f"{len(useful_post_event_links_puerto_rico)}"
        assert puertoRicoBox.left == left
        assert puertoRicoBox.right == right
        assert puertoRicoBox.top == top
        assert puertoRicoBox.bottom == bottom
    
    def test_get_list_of_bounds_for_hurricane(self):
        hurricane_name = "test"
        d = get_list_of_bounds_for_hurricane(hurricane_name, False)
        assert len(d["pre"]) == 2, f"Should have 2 valid pre-event links in test_file_list, get {len(d['pre'])} instead"
        assert len(d["post"]) == 2, f"Should have 2 valid post-event links in test_file_list, get {len(d['post'])} instead"


class TestVectorDataUtils(unittest.TestCase):
    def test_get_vector_data_links(self):
        links = get_vector_data_links("irma", False)
        assert len(links) == 3, f"Expect 3 links but found {len(links)} links instead"

suite = unittest.TestLoader().loadTestsFromTestCase(TestVectorDataUtils)