import os
import sys
import glob
import requests

from argparse import ArgumentParser
from collections import defaultdict, OrderedDict

"""
config = {
    "sites": {
        "3": "zoink.it",
        "4": "torrage.com",
        "5": "torcache.net"
    }
}
"""
from uploader_config import config

class TorrentUploader():
    def __init__(self, torrents, sites, output_file=None):
        self.torrents = torrents
        self.sites = sites
        self.out = open(output_file, "a") if output_file else None

    def _write_output(self, ln):
        if self.out is not None:
            self.out.write("%s\n" % ln)
            self.out.flush()

    def _cache_torrent(self, url, torrent_path):
        fp = open(torrent_path, "r")
        payload = {
            "torrent": ("torrent", fp, "application/x-bittorrent")
        }
        info_hash = None
        try:
            res = requests.post(url, files=payload)
            info_hash = res.text.strip()
        except Exception as e:
            pass

        fp.close()
        #print str(info_hash)
        return info_hash

    def go(self):
        outputs = OrderedDict()
        for torrent in self.torrents:
            for site in self.sites:
                #result = self._cache_torrent("http://%s/autoupload.php" % self.sites[site], torrent)
                result = self._cache_torrent("%s" % self.sites[site], torrent)
                if result is None:
                    print("Warning: Failed to upload torrent '%s' to '%s'!" % (torrent, self.sites[site]))
                    continue
                else:
                    print("Uploaded torrent '%s' to '%s'!" % (torrent, self.sites[site]))

                if torrent not in outputs:
                    outputs[torrent] = OrderedDict()

                outputs[torrent][site] = result
                if result != "" and "hash" not in outputs[torrent]:
                    outputs[torrent]["hash"] = result


        html_output = dict()

        for torrent, sites in outputs.iteritems():
            info_hash = sites["hash"]
            html_strs = []
            html_strs.append('<a href="/torrents/%s">1</a> ' % os.path.basename(torrent))
            for i in range(2, 6):
                if str(i) in sites:
                    html_strs.append('<a href="%s/torrent/%s.torrent">%s</a> ' % ("/".join(self.sites[str(i)].split("/")[:-1]), info_hash, str(i)))
                else:
                    html_strs.append("%s " % str(i))
            html_strs.append('<a href="magnet:?xt=urn:btih:%s">6</a> ' % info_hash)

            html = "   " + "".join(html_strs) + "   "
            self._write_output(html)
            html_output[torrent] = html

        return html_output


def main(argv):
    parser = ArgumentParser()
    parser.add_argument("-f", "--folder", action="store", dest="folder", help="The folder of torrent files to cache.", default=None)
    parser.add_argument("-o", "--output", action="store", dest="output", help="The file to output generated HTML to.", default=None)
    args = parser.parse_args()


    if not args.folder or not args.output:
        print("Error: Folder and output are required!")
        return 1

    folder = args.folder
    output = args.output

    if not os.path.isdir(folder):
        print("Error: Input folder doesn't exist or is not a folder!")
        return 1

    files = glob.glob(os.path.join(folder, "*.torrent"))

    uploader = TorrentUploader(files, config["sites"], output)
    html = uploader.go()
    #with open(output, "w") as fp:
    #    fp.write(html)
    final_str = ""
    for file, htmls in html.iteritems():
        final_str += "%s: \n" + htmls + "\n"


    #print final_str
    with open(output, "w") as fp:
        fp.write(final_str)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
