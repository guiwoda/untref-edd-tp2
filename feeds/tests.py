from django.test import TestCase

# Create your tests here.
class TestFeedReader(TestCase):
    def test_download_xml_from_feed(self):
        reader = FeedReader