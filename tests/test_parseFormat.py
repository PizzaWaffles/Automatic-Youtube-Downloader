from unittest import TestCase
from main import parseFormat


class TestParseFormat(TestCase):

    def test_parseFormat(self):

        # formating, name="", date="", title="", chID="", id=""
        name = "name"
        date = "date"
        title = "title"
        chID = "chID"
        id = ""
        format = "%NAME%UPLOAD_DATE%TITLE%CHANNEL_ID%VIDEO_ID"

        self.assertEqual(parseFormat(format, name, date, title, chID, id), "namedatetitlechID")
