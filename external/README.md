## Makefile download targets

**IN BRIEF**: Makefile history has been modified, appending targets to download archives from SourceForge with wget instead of requiring source tarballs to be bundled directly.

This folder now contains three core git submodules: *imagen*, *param* and *paramtk*. If you cloned Topographica using the ```--recursive``` option, these will have been fetched. If you haven't, you are likely to run into import errors which may be fixed by running:

``` git submodule update --init ```

### History

In its original form, the external subfolder was hosted in an SVN repository and contained source archives (typically tarballs) of external dependencies used by Topographica and its users. When migrating to GitHub, it was decided that hosting large numbers of binary files was not appropriate. For this reason, all versions of these binaries have been removed and hosted on Sourceforge (including diffs where necessary) and all Makefiles updated to ensure all checkouts should continue to work appropriately.

Every Makefiles in the history has had generic targets appended. These targets fetch the compressed source archives from [external-full-history](https://sourceforge.net/projects/topographica/files/external-full-history/) on Sourceforge if the files do not already exist in the directory. This is standard behaviour using this Makefile when working with Topographica from Github.

This approach assumes that all Makefiles in the history correctly list the necessary archive files listed as dependencies for all the desired make targets. If you encounter problems installing external dependencies from an old Makefile in the history, consider either fixing the broken targets, fetching the appropriate SVN revision of Topographica directly from Sourceforge or consult the [*ioam/svn-history*](https://github.com/ioam/svn-history) repository.