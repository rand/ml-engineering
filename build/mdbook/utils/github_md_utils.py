"""
The utils in this module replicate github logic, which means it may or may not work for other markdown
"""

import re
from pathlib import Path

# matches ("Markdown text", Link) in [Markdown text](Link)
re_md_link_2_parts = re.compile(r"""
^
\[
([^]]+)
\]
\(
([^)]+)
\)
$
""", re.VERBOSE)

# matches one or more '[Markdown text](Link)' patterns
re_md_link_full = re.compile(r"""
(
\[
[^]]+
\]
\(
[^)]+
\)
)
""", re.VERBOSE|re.MULTILINE)

img_exts = ["jpg", "jpeg", "png"]
re_link_images = re.compile("(" + "|".join(img_exts) + ")", re.VERBOSE|re.MULTILINE|re.IGNORECASE)

cwd_abs_path = Path.cwd()

def md_is_relative_link(link):
    # skip any protocol:/ based links - what remains should be a relative local links - relative to
    # the root of the project or to any of the local pages
    if ":/" in link:
        return False
    return True

def md_process_local_links(para, callback, **kwargs):
    """
    parse the paragraph to detect local markdown links, process those through callback and put them
    back into the paragraph and return the result
    """
    return re.sub(re_md_link_full,
                  lambda x: callback(x.group(), **kwargs) if md_is_relative_link(x.group()) else x.group(),
                  para)


def md_link_break_up(text):
    """
    text = [Markdown text](Link.md)
    returns ("markdown text", "link.md", None)

    text = [Markdown text](Link.md#bar)
    returns ("markdown text", "link.md", "bar")

    text = [Markdown text](Link/#bar)
    returns ("markdown text", "link/", "bar")
    """
    match = re.findall(re_md_link_2_parts, text)
    if match:
        link_text, full_link = match[0]

        # split full_link into link and anchor parts
        link_parts = full_link.split("#")
        link = link_parts[0]
        anchor = link_parts[1] if len(link_parts)==2 else None
        return (link_text, link, anchor)
    else:
        raise ValueError(f"invalid md link markup: {text}")


def md_link_build(link_text, link, anchor=None):
    """
    returns [link_text](link)
    """
    full_link = link
    if anchor is not None:
        full_link += f"#{anchor}"

    return f"[{link_text}]({full_link})"


def resolve_rel_link(link, cwd_rel_path):
    """ resolves all sorts of ./, ../foobar and returns a relative to the repo root relative link
    this is useful if a repo url needs to be prepended

    XXX: it assumes the program is run from the root of the repo
    """
    link = (Path(cwd_rel_path) / Path(link)).resolve().relative_to(cwd_abs_path)
    return str(link)

def md_expand_links(text, cwd_rel_path, repo_url=""):
    """
    Perform link rewrites as following:
    - if the link ends in .md or contains protocol :// return unmodified
    - convert relative link shortcuts into full links, e.g. chapter/ => chapter/README.md
    - if the link is not for .md or images, it's not going to be in the pdf, so resolve it and point
      to its url at the the repo

    """
    link_text, link, anchor = md_link_break_up(text)

    #print(link_text, link, anchor)

    # skip explicit .md links and external links
    if len(link) > 0  and (link.endswith(".md") or re.search(r'^\w+://', link)):
        return text

    link = Path(link)
    try_link = link / "README.md"

    full_path = cwd_rel_path / try_link
    if full_path.exists():
        link = str(try_link)
    else:
        link = str(link)

        # leave the images local for pdf rendering, but for the rest of the file (scripts,
        # reports, etc.)
        # prepend the repo base url, while removing ./ relative prefix if any
        if not re.search(re_link_images, link):
            link = resolve_rel_link(link, cwd_rel_path)
            link = repo_url + "/" + link

    return md_link_build(link_text, link, anchor)


def md_rename_relative_links(text, cwd_rel_path, src, dst):
    """
    Perform link rewrites as following:
    - if the link contains protocol :// do nothing

    """
    link_text, link, anchor = md_link_break_up(text)

    # skip external links
    if len(link) > 0 and re.search(r'^\w+://', link):
        return text

    print(link_text, link, anchor)
    print(cwd_rel_path, src, dst)

    full_path = str(cwd_rel_path / link)
    print("FULL ORIG", full_path)

    new_path = full_path.replace(src, dst)
    print("FULL  NEW", new_path)

    if new_path != full_path:
        print("SHORT NEW", new_path)
        link = new_path.replace(str(cwd_rel_path) + "/", "")

    return md_link_build(link_text, link, anchor)



def md_convert_md_target_to_html(text):
    """
    convert .md target to .html target

    - chapter/doc.md => chapter/doc.html
    """
    link_text, link, anchor = md_link_break_up(text)
    link = re.sub("\.md$", ".html", link)
    return md_link_build(link_text, link, anchor)


def md_header_to_anchor(text):
    """
    Convert "#" headers into anchors
    # This is title => this-is-title
    """
    orig_text = text
    # lowercase
    text = text.lower()
    # keep only a subset of chars
    text = re.sub(r"[^-_a-z0-9\s]", r"", text, flags=re.IGNORECASE)
    # spaces2dashes
    text = re.sub(r"\s", r"-", text, flags=re.IGNORECASE)
    # leading/trailing cleanup
    text = re.sub(r"(^-+|-+$)", r"", text, flags=re.IGNORECASE)

    return text

def md_header_to_md_link(text, link=''):
    """
    Convert "#" headers into an md link

    # This is title => [This is title](link#this-is-title)

    if `link` is not passed or it's "" it'll generate a local anchored link
    """
    anchor = md_header_to_anchor(text)
    return f"[{text}]({link}#{anchor})"

if __name__ == "__main__":

    # # run to test some of these utils
    # para = 'bb [Markdown text](foo.md#tar) aaa bb [Markdown text2](foo/#bar) aaa [Markdown text3](http://ex.com/foo/#bar)'
    # print(para)
    # para = md_process_local_links(para, md_expand_links, cwd_rel_path=".")
    # print(para)

    # para = 'bb [Part 1](../Part1/) [Part 1](../Part1) [Local](#local) ![image](image.png)'
    # print(para)
    # para = md_process_local_links(para, md_expand_links, cwd_rel_path=".")
    # print(para)


    para = 'bb [Markdown text](foo.md#tar) aaa bb [Markdown text2](foo/#bar) aaa [Markdown text3](../foo/bar)'
    print(para)
    para = md_process_local_links(para, md_rename_relative_links, cwd_rel_path=Path("."), src="foo", dst="tar")
    print(para)
