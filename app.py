Microsoft Windows [Version 10.0.19045.7417]
(c) Microsoft Corporation. All rights reserved.

D:\OneDrive\Documents\GitHub\Wealth-Tracker-JSR>git add app.py

D:\OneDrive\Documents\GitHub\Wealth-Tracker-JSR>git commit -m "Fix UI date crash with session state init"
[main 416213c] Fix UI date crash with session state init
 1 file changed, 28 insertions(+), 15 deletions(-)

D:\OneDrive\Documents\GitHub\Wealth-Tracker-JSR>git push -u origin maingit commit -m "Fix UI date crash with session state init
error: unknown switch `m'
usage: git push [<options>] [<repository> [<refspec>...]]

    -v, --[no-]verbose    be more verbose
    -q, --[no-]quiet      be more quiet
    --[no-]repo <repository>
                          repository
    --[no-]all            push all branches
    --[no-]branches       alias of --all
    --[no-]mirror         mirror all refs
    -d, --[no-]delete     delete refs
    --[no-]tags           push tags (can't be used with --all or --branches or --mirror)
    -n, --[no-]dry-run    dry run
    --[no-]porcelain      machine-readable output
    -f, --[no-]force      force updates
    --[no-]force-with-lease[=<refname>:<expect>]
                          require old value of ref to be at this value
    --[no-]force-if-includes
                          require remote updates to be integrated locally
    --[no-]recurse-submodules (check|on-demand|no)
                          control recursive pushing of submodules
    --[no-]thin           use thin pack
    --[no-]receive-pack <receive-pack>
                          receive pack program
    --[no-]exec <receive-pack>
                          receive pack program
    -u, --[no-]set-upstream
                          set upstream for git pull/status
    --[no-]progress       force progress reporting
    --[no-]prune          prune locally removed refs
    --no-verify           bypass pre-push hook
    --verify              opposite of --no-verify
    --[no-]follow-tags    push missing but relevant tags
    --[no-]signed[=(yes|no|if-asked)]
                          GPG sign the push
    --[no-]atomic         request atomic transaction on remote side
    -o, --[no-]push-option <server-specific>
                          option to transmit
    -4, --ipv4            use IPv4 addresses only
    -6, --ipv6            use IPv6 addresses only


D:\OneDrive\Documents\GitHub\Wealth-Tracker-JSR>git push -u origin main
Enumerating objects: 5, done.
Counting objects: 100% (5/5), done.
Delta compression using up to 4 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (3/3), 964 bytes | 964.00 KiB/s, done.
Total 3 (delta 1), reused 0 (delta 0), pack-reused 0 (from 0)
remote: Resolving deltas: 100% (1/1), completed with 1 local object.
To https://github.com/psr1510/Wealth-Tracker-JSR.git
   966c760..416213c  main -> main
branch 'main' set up to track 'origin/main'.

D:\OneDrive\Documents\GitHub\Wealth-Tracker-JSR>
D:\OneDrive\Documents\GitHub\Wealth-Tracker-JSR>git add app.py

D:\OneDrive\Documents\GitHub\Wealth-Tracker-JSR>git commit -m "Restore full dashboard
[main 7e1ef7a] Restore full dashboard
 1 file changed, 129 insertions(+), 36 deletions(-)

D:\OneDrive\Documents\GitHub\Wealth-Tracker-JSR>git push -u origin main
Enumerating objects: 5, done.
Counting objects: 100% (5/5), done.
Delta compression using up to 4 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (3/3), 2.77 KiB | 2.77 MiB/s, done.
Total 3 (delta 1), reused 0 (delta 0), pack-reused 0 (from 0)
remote: Resolving deltas: 100% (1/1), completed with 1 local object.
To https://github.com/psr1510/Wealth-Tracker-JSR.git
   416213c..7e1ef7a  main -> main
branch 'main' set up to track 'origin/main'.

D:\OneDrive\Documents\GitHub\Wealth-Tracker-JSR>git add app.py

D:\OneDrive\Documents\GitHub\Wealth-Tracker-JSR>git commit -m "Fix date initialization crash
[main df5032c] Fix date initialization crash
 1 file changed, 97 insertions(+), 10 deletions(-)

D:\OneDrive\Documents\GitHub\Wealth-Tracker-JSR>git push -u origin main
Enumerating objects: 5, done.
Counting objects: 100% (5/5), done.
Delta compression using up to 4 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (3/3), 1.88 KiB | 1.88 MiB/s, done.
Total 3 (delta 2), reused 0 (delta 0), pack-reused 0 (from 0)
remote: Resolving deltas: 100% (2/2), completed with 2 local objects.
To https://github.com/psr1510/Wealth-Tracker-JSR.git
   7e1ef7a..df5032c  main -> main
branch 'main' set up to track 'origin/main'.

D:\OneDrive\Documents\GitHub\Wealth-Tracker-JSR>git add WealthDatabase.db TransactionsLatestCAS.xlsx

D:\OneDrive\Documents\GitHub\Wealth-Tracker-JSR>git commit -m "Upload latest data files"
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   app.py

no changes added to commit (use "git add" and/or "git commit -a")

D:\OneDrive\Documents\GitHub\Wealth-Tracker-JSR>git push -u origin maingit commit -m "Upload latest data files
error: unknown switch `m'
usage: git push [<options>] [<repository> [<refspec>...]]

    -v, --[no-]verbose    be more verbose
    -q, --[no-]quiet      be more quiet
    --[no-]repo <repository>
                          repository
    --[no-]all            push all branches
    --[no-]branches       alias of --all
    --[no-]mirror         mirror all refs
    -d, --[no-]delete     delete refs
    --[no-]tags           push tags (can't be used with --all or --branches or --mirror)
    -n, --[no-]dry-run    dry run
    --[no-]porcelain      machine-readable output
    -f, --[no-]force      force updates
    --[no-]force-with-lease[=<refname>:<expect>]
                          require old value of ref to be at this value
    --[no-]force-if-includes
                          require remote updates to be integrated locally
    --[no-]recurse-submodules (check|on-demand|no)
                          control recursive pushing of submodules
    --[no-]thin           use thin pack
    --[no-]receive-pack <receive-pack>
                          receive pack program
    --[no-]exec <receive-pack>
                          receive pack program
    -u, --[no-]set-upstream
                          set upstream for git pull/status
    --[no-]progress       force progress reporting
    --[no-]prune          prune locally removed refs
    --no-verify           bypass pre-push hook
    --verify              opposite of --no-verify
    --[no-]follow-tags    push missing but relevant tags
    --[no-]signed[=(yes|no|if-asked)]
                          GPG sign the push
    --[no-]atomic         request atomic transaction on remote side
    -o, --[no-]push-option <server-specific>
                          option to transmit
    -4, --ipv4            use IPv4 addresses only
    -6, --ipv6            use IPv6 addresses only


D:\OneDrive\Documents\GitHub\Wealth-Tracker-JSR>git push -u origin main
branch 'main' set up to track 'origin/main'.
Everything up-to-date

D:\OneDrive\Documents\GitHub\Wealth-Tracker-JSR>