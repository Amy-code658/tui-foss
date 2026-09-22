"""Byte's Linux Adventure - 15 Adventure Levels & Quests.

Friendly, playful exploration scenarios teaching Linux fundamentals step by step
with interactive 4-option questions to deduce and practice real commands.
"""

from __future__ import annotations

from typing import Dict

from cybershell.contracts import Item, Objective, Quest


def get_sector_quests() -> Dict[int, Quest]:
    """Returns a dictionary mapping level IDs (0-14 for Levels 1-15) to their Quests."""
    quests: Dict[int, Quest] = {}

    # -------------------------------------------------------------------------
    # LEVEL 1: LOOK AROUND (pwd, ls)
    # -------------------------------------------------------------------------
    quests[0] = Quest(
        id="level_01",
        sector_id=0,
        sector_name="Look Around",
        npc_name="Byte",
        lore="You just arrived in your new Linux world! Let's get our bearings and see what is nearby.",
        dialogue=[
            "Hello! I'm Byte, your friendly guide.",
            "Whenever you arrive in a new folder, two commands are super handy: 'pwd' and 'ls'.",
            "Let's see if you can figure out which command checks your location!",
        ],
        objectives=[
            Objective(
                id="obj_1_1",
                description="Determine your current working directory location.",
                hint="Think about the command that stands for 'Print Working Directory'.",
                command="pwd",
                syntax="pwd",
                explanation="Prints your current working directory path.",
                predicate_type="cwd_equals",
                predicate_target="~",
                xp_reward=50,
                hints=[
                    "Which command prints your current folder location?",
                    "It stands for 'Print Working Directory'.",
                    "Type: pwd (or select option B)",
                ],
                scenario="You just arrived in the shell. Where are you in the directory tree?",
                question="Which Linux command displays your current working directory path?",
                options=[
                    "ls       - List files in current folder",
                    "pwd      - Print working directory path",
                    "cd       - Change current directory",
                    "whoami   - Display current logged in user",
                ],
                correct_option="B",
            ),
            Objective(
                id="obj_1_2",
                description="Inspect and list all visible files in this folder.",
                hint="Think of the two-letter command used to 'list' items.",
                command="ls",
                syntax="ls",
                explanation="Lists the files and folders in your current location.",
                predicate_type="cwd_equals",
                predicate_target="~",
                xp_reward=50,
                hints=[
                    "Use the list command to see nearby files and folders.",
                    "The command is just two letters: l and s.",
                    "Type: ls (or select option A)",
                ],
                scenario="Now look around. Something useful is waiting nearby.",
                question="Which command lists the files and directories in your current folder?",
                options=[
                    "ls       - List directory contents",
                    "cat      - Display file contents",
                    "touch    - Create a new file",
                    "mkdir    - Make a new folder",
                ],
                correct_option="A",
            ),
        ],
        reward_item=Item(
            id="item_compass",
            name="Wooden Compass 🧭",
            description="Helps you always find your bearings in any folder.",
            category="tool",
            rarity="common",
        ),
        reward_xp=100,
        environment_tree={
            "welcome.txt": "Welcome to your Linux Adventure! There is so much to explore.\n",
            "notes.txt": "Tip: 'pwd' tells you where you are, and 'ls' shows you what's around!\n",
        },
    )

    # -------------------------------------------------------------------------
    # LEVEL 2: FOLLOW THE PATH (cd, ..)
    # -------------------------------------------------------------------------
    quests[1] = Quest(
        id="level_02",
        sector_id=1,
        sector_name="Follow the Path",
        npc_name="Byte",
        lore="Look! There is a cozy garden folder right here. Let's step inside and explore it.",
        dialogue=[
            "Moving between folders is just like walking through rooms in a house.",
            "Let's see which command helps you step into another folder!",
        ],
        objectives=[
            Objective(
                id="obj_2_1",
                description="Navigate inside the 'garden' subfolder.",
                hint="Use the change directory command followed by the folder name.",
                command="cd",
                syntax="cd garden",
                explanation="Changes your current directory to the garden folder.",
                predicate_type="cwd_equals",
                predicate_target="garden",
                xp_reward=50,
                hints=[
                    "Use the change directory command 'cd' with 'garden'.",
                    "Remember to put a space after 'cd'.",
                    "Type: cd garden (or select option B)",
                ],
                scenario="There is a subfolder named 'garden'. How do we step inside?",
                question="Which command will move your terminal session into the 'garden' folder?",
                options=[
                    "open garden   - Open folder in desktop viewer",
                    "cd garden     - Change directory into garden",
                    "ls garden     - List garden contents without moving",
                    "mv garden     - Move or rename the garden folder",
                ],
                correct_option="B",
            ),
            Objective(
                id="obj_2_2",
                description="Return up one level back to your home directory.",
                hint="In Linux, '..' represents the parent directory one level above.",
                command="cd",
                syntax="cd ..",
                explanation="'..' refers to the parent folder one level up.",
                predicate_type="cwd_equals",
                predicate_target="~",
                xp_reward=50,
                hints=[
                    "Two dots (..) represent the folder above you.",
                    "Type 'cd ..' with a space between cd and ..",
                    "Type: cd .. (or select option A)",
                ],
                scenario="You finished admiring the garden! How do you step back outside?",
                question="Which command navigates one level up to the parent directory?",
                options=[
                    "cd ..     - Move up one directory level",
                    "cd /      - Jump all the way to system root",
                    "back      - Return to previous history",
                    "exit      - Close the terminal session",
                ],
                correct_option="A",
            ),
        ],
        reward_item=Item(
            id="item_shoes",
            name="Walking Shoes 👟",
            description="Comfy shoes for walking through directories.",
            category="clothing",
            rarity="common",
        ),
        reward_xp=100,
        environment_tree={
            "garden": {
                "flowers.txt": "Sunflowers, daisies, and lavender grow here peacefully. 🌸\n",
                "bench.txt": "A warm wooden bench where you can sit and code.\n",
            },
        },
    )

    # -------------------------------------------------------------------------
    # LEVEL 3: READ THE NOTE (cat, less)
    # -------------------------------------------------------------------------
    quests[2] = Quest(
        id="level_03",
        sector_id=2,
        sector_name="Read the Note",
        npc_name="Penny",
        lore="Someone left a friendly letter named 'welcome.txt' on the desk. Let's read what it says!",
        dialogue=[
            "Hi there! I'm Penny the archivist.",
            "Files often contain notes, scrolls, and configuration data.",
            "Can you figure out which command prints file contents onto your screen?",
        ],
        objectives=[
            Objective(
                id="obj_3_1",
                description="Inspect the contents of 'welcome.txt' on screen.",
                hint="Think of the command named after a feline friend, or the pager 'less'.",
                command="cat,less",
                syntax="cat <filename>",
                explanation="Outputs the text inside a file right onto your terminal.",
                predicate_type="file_read",
                predicate_target="welcome.txt",
                xp_reward=100,
                hints=[
                    "The 'cat' command prints file contents to your terminal.",
                    "Specify the file name after the command.",
                    "Type: cat welcome.txt (or select option B)",
                ],
                scenario="A friendly note named 'welcome.txt' is waiting on the desk.",
                question="Which command reads and prints the text of 'welcome.txt' directly to your screen?",
                options=[
                    "read welcome.txt   - Open in editor prompt",
                    "cat welcome.txt    - Output file contents to terminal",
                    "open welcome.txt   - Launch system desktop viewer",
                    "echo welcome.txt   - Print the literal filename text",
                ],
                correct_option="B",
            ),
        ],
        reward_item=Item(
            id="item_magnifier",
            name="Magnifying Glass 🔍",
            description="Helps you inspect file contents with ease.",
            category="tool",
            rarity="uncommon",
        ),
        reward_xp=100,
        environment_tree={
            "welcome.txt": "Great job! Reading files is one of the most essential Linux skills.\nKeep exploring! 🌱\n",
        },
    )

    # -------------------------------------------------------------------------
    # LEVEL 4: HIDDEN STUFF (ls -a)
    # -------------------------------------------------------------------------
    quests[3] = Quest(
        id="level_04",
        sector_id=3,
        sector_name="Hidden Stuff",
        npc_name="Byte",
        lore="In Linux, any file that starts with a dot '.' is hidden from regular view. Let's find what's hiding!",
        dialogue=[
            "Normal 'ls' keeps hidden dotfiles out of your way.",
            "Passing a special flag will reveal everything in the room!",
        ],
        objectives=[
            Objective(
                id="obj_4_1",
                description="Reveal all hidden files starting with a dot in this folder.",
                hint="Pass the flag for 'all' to your list command.",
                command="ls",
                syntax="ls -a",
                explanation="Lists all directory contents, including hidden files beginning with a dot.",
                predicate_type="pattern_matched",
                predicate_target="ls",
                predicate_expected="-a",
                xp_reward=50,
                hints=[
                    "Use the '-a' flag with 'ls' to show all files.",
                    "Make sure there is a space between ls and -a.",
                    "Type: ls -a (or select option A)",
                ],
                scenario="Someone hid a secret file here. Standard 'ls' won't show it!",
                question="Which command lists ALL files including hidden dotfiles?",
                options=[
                    "ls -a      - List all files including hidden dotfiles",
                    "ls -h      - List files with human-readable sizes",
                    "ls -l      - Long format listing without hidden files",
                    "find .     - Search all files recursively",
                ],
                correct_option="A",
            ),
            Objective(
                id="obj_4_2",
                description="Read the hidden file '.secret_recipe'.",
                hint="Remember to include the leading dot in the filename when using cat.",
                command="cat,less",
                syntax="cat .secret_recipe",
                explanation="Reads the hidden file contents.",
                predicate_type="file_read",
                predicate_target=".secret_recipe",
                xp_reward=50,
                hints=[
                    "Don't forget the leading dot in the filename!",
                    "Type: cat .secret_recipe",
                    "Type: cat .secret_recipe (or select option B)",
                ],
                scenario="You spotted '.secret_recipe'! What delicious secret is inside?",
                question="Which command will read the contents of the hidden file '.secret_recipe'?",
                options=[
                    "view recipe          - Open text viewer",
                    "cat .secret_recipe   - Output hidden file contents",
                    "cat secret_recipe    - Look for non-hidden file",
                    "echo .secret_recipe  - Print the filename string",
                ],
                correct_option="B",
            ),
        ],
        reward_item=Item(
            id="item_flashlight",
            name="Pocket Flashlight 🔦",
            description="Shines bright light onto hidden dotfiles.",
            category="tool",
            rarity="uncommon",
        ),
        reward_xp=100,
        environment_tree={
            ".secret_recipe": "Secret Cookie Recipe: 2 cups flour, 1 cup chocolate chips, lots of love! 🍪\n",
            "public_notes.txt": "Nothing secret here... or is there?\n",
        },
    )

    # -------------------------------------------------------------------------
    # LEVEL 5: FIND IT (find)
    # -------------------------------------------------------------------------
    quests[4] = Quest(
        id="level_05",
        sector_id=4,
        sector_name="Find It",
        npc_name="Penny",
        lore="A key has been misplaced somewhere deep inside nested subdirectories! Let's track it down.",
        dialogue=[
            "When files are scattered across many folders, searching manually takes forever.",
            "The 'find' command can scan entire directory trees in a flash!",
        ],
        objectives=[
            Objective(
                id="obj_5_1",
                description="Locate 'lost_key.txt' anywhere in the current directory tree.",
                hint="Use 'find .' with the '-name' option followed by \"lost_key.txt\".",
                command="find",
                syntax='find . -name "lost_key.txt"',
                explanation="Searches the directory hierarchy for files matching a name pattern.",
                predicate_type="pattern_matched",
                predicate_target="find",
                predicate_expected="lost_key.txt",
                xp_reward=100,
                hints=[
                    "Use 'find' starting from current folder '.' with '-name'.",
                    'Try: find . -name "lost_key.txt"',
                    'Type: find . -name "lost_key.txt" (or select option B)',
                ],
                scenario="A brass key named 'lost_key.txt' is lost somewhere in a subfolder.",
                question="Which command will search the current directory tree for a file named 'lost_key.txt'?",
                options=[
                    "search lost_key.txt              - Query system desktop index",
                    'find . -name "lost_key.txt"      - Find files matching name in tree',
                    "locate lost_key.txt              - Query pre-built locate database",
                    "grep lost_key.txt                - Search text inside file contents",
                ],
                correct_option="B",
            ),
        ],
        reward_item=Item(
            id="item_metal_detector",
            name="Mini Metal Detector 🪙",
            description="Beeps enthusiastically when lost files are nearby.",
            category="tool",
            rarity="uncommon",
        ),
        reward_xp=100,
        environment_tree={
            "attic": {
                "boxes": {
                    "lost_key.txt": "🔑 You found the lost brass key! It opens new possibilities.\n",
                },
            },
        },
    )

    # -------------------------------------------------------------------------
    # LEVEL 6: SEARCH INSIDE (grep)
    # -------------------------------------------------------------------------
    quests[5] = Quest(
        id="level_06",
        sector_id=5,
        sector_name="Search Inside",
        npc_name="Fern",
        lore="We have a big diary here with dozens of entries. Somewhere inside, the word 'magic' is mentioned!",
        dialogue=[
            "Greetings! I'm Fern, the garden philosopher.",
            "Instead of reading hundreds of lines, 'grep' searches text for specific words!",
        ],
        objectives=[
            Objective(
                id="obj_6_1",
                description="Search for lines containing 'magic' inside 'diary.txt'.",
                hint="Use the pattern search command 'grep' with the word and filename.",
                command="grep",
                syntax='grep "magic" diary.txt',
                explanation="Searches for lines containing matching text in a file.",
                predicate_type="pattern_matched",
                predicate_target="grep",
                predicate_expected="magic",
                xp_reward=100,
                hints=[
                    "Use 'grep' followed by the search term and the file name.",
                    'Try: grep "magic" diary.txt',
                    'Type: grep "magic" diary.txt (or select option B)',
                ],
                scenario="The diary is huge! Find the lines mentioning 'magic'.",
                question="Which command searches inside 'diary.txt' for lines containing 'magic'?",
                options=[
                    'find "magic" diary.txt         - Search filesystem for files',
                    'grep "magic" diary.txt         - Search lines matching pattern in file',
                    'cat diary.txt | find "magic"    - Invalid find usage on stream',
                    'search diary.txt "magic"       - Query diary text',
                ],
                correct_option="B",
            ),
        ],
        reward_item=Item(
            id="item_bookmark",
            name="Pressed Clover Bookmark 🍀",
            description="Quickly marks the exact lines you need to remember.",
            category="curio",
            rarity="uncommon",
        ),
        reward_xp=100,
        environment_tree={
            "diary.txt": (
                "Day 1: Planted tomatoes.\n"
                "Day 2: Watered the sprouts.\n"
                "Day 3: The morning dew felt like pure magic on the leaves.\n"
                "Day 4: Weeded the beds.\n"
            ),
        },
    )

    # -------------------------------------------------------------------------
    # LEVEL 7: COPY & MOVE (cp, mv)
    # -------------------------------------------------------------------------
    quests[6] = Quest(
        id="level_07",
        sector_id=6,
        sector_name="Copy & Move",
        npc_name="Byte",
        lore="Organizing files keeps our adventure clean! Let's practice duplicating and moving files.",
        dialogue=[
            "Need a backup? 'cp' duplicates a file.",
            "Need to relocate or rename? 'mv' moves it to a new home!",
        ],
        objectives=[
            Objective(
                id="obj_7_1",
                description="Make a duplicate copy of 'seed.txt' named 'flower.txt'.",
                hint="Use the copy command 'cp' with the source and target filenames.",
                command="cp",
                syntax="cp seed.txt flower.txt",
                explanation="Copies source file to destination.",
                predicate_type="file_exists",
                predicate_target="flower.txt",
                xp_reward=50,
                hints=[
                    "The copy command is 'cp'.",
                    "Syntax: cp <source> <destination>",
                    "Type: cp seed.txt flower.txt (or select option A)",
                ],
                scenario="You have 'seed.txt'. Create a duplicate named 'flower.txt'.",
                question="Which command copies 'seed.txt' to create a new file named 'flower.txt'?",
                options=[
                    "cp seed.txt flower.txt     - Copy source to destination",
                    "mv seed.txt flower.txt     - Rename or move file",
                    "dup seed.txt flower.txt    - Duplicate file",
                    "ln seed.txt flower.txt     - Create link to file",
                ],
                correct_option="A",
            ),
            Objective(
                id="obj_7_2",
                description="Move 'flower.txt' into the 'garden' folder.",
                hint="Use the move command 'mv' with the file and destination folder.",
                command="mv",
                syntax="mv flower.txt garden/flower.txt",
                explanation="Moves a file into a destination directory.",
                predicate_type="file_exists",
                predicate_target="garden/flower.txt",
                xp_reward=50,
                hints=[
                    "The move command is 'mv'.",
                    "Syntax: mv <file> <destination_folder>/",
                    "Type: mv flower.txt garden/flower.txt (or select option B)",
                ],
                scenario="Now relocate 'flower.txt' into the 'garden/' folder.",
                question="Which command moves 'flower.txt' into the 'garden/' folder?",
                options=[
                    "cp flower.txt garden/     - Copy file into folder",
                    "mv flower.txt garden/     - Move file into directory",
                    "put flower.txt garden/    - Transfer file",
                    "rm flower.txt garden/     - Delete file",
                ],
                correct_option="B",
            ),
        ],
        reward_item=Item(
            id="item_trowel",
            name="Gardener's Trowel 🪴",
            description="Perfect for moving seedlings from pot to garden.",
            category="tool",
            rarity="common",
        ),
        reward_xp=100,
        environment_tree={
            "seed.txt": "A tiny sunflower seed full of potential.\n",
            "garden": {},
        },
    )

    # -------------------------------------------------------------------------
    # LEVEL 8: CLEAN UP (mkdir, touch, rm)
    # -------------------------------------------------------------------------
    quests[7] = Quest(
        id="level_08",
        sector_id=7,
        sector_name="Clean Up",
        npc_name="Byte",
        lore="Let's build a greenhouse, plant a sprout, and clean up some old trash!",
        dialogue=[
            "'mkdir' creates new folders.",
            "'touch' creates fresh empty files.",
            "'rm' removes old files you no longer need.",
        ],
        objectives=[
            Objective(
                id="obj_8_1",
                description="Create a new folder named 'greenhouse'.",
                hint="Use the make directory command 'mkdir'.",
                command="mkdir",
                syntax="mkdir greenhouse",
                explanation="Creates a new directory.",
                predicate_type="file_exists",
                predicate_target="greenhouse",
                xp_reward=35,
                hints=[
                    "The make directory command is 'mkdir'.",
                    "Type: mkdir greenhouse (or select option B)",
                    "Type: mkdir greenhouse",
                ],
                scenario="Build a fresh folder named 'greenhouse'.",
                question="Which command creates a new directory named 'greenhouse'?",
                options=[
                    "newdir greenhouse      - Create new directory",
                    "mkdir greenhouse       - Make a new directory",
                    "touch greenhouse       - Create a new empty file",
                    "create greenhouse      - Allocate new folder",
                ],
                correct_option="B",
            ),
            Objective(
                id="obj_8_2",
                description="Create an empty file named 'sprout.txt' inside 'greenhouse/'.",
                hint="Use 'touch' with the relative path 'greenhouse/sprout.txt'.",
                command="touch",
                syntax="touch greenhouse/sprout.txt",
                explanation="Creates an empty file if it does not already exist.",
                predicate_type="file_exists",
                predicate_target="greenhouse/sprout.txt",
                xp_reward=35,
                hints=[
                    "Use 'touch' followed by the path.",
                    "Try: touch greenhouse/sprout.txt",
                    "Type: touch greenhouse/sprout.txt (or select option A)",
                ],
                scenario="Plant a new sprout inside the greenhouse.",
                question="Which command creates a new file 'sprout.txt' inside the 'greenhouse/' directory?",
                options=[
                    "touch greenhouse/sprout.txt    - Create empty file",
                    "mkdir greenhouse/sprout.txt    - Make subfolder",
                    "write greenhouse/sprout.txt    - Open text editor",
                    "cat greenhouse/sprout.txt      - Display file",
                ],
                correct_option="A",
            ),
            Objective(
                id="obj_8_3",
                description="Remove the unwanted file 'old_trash.txt'.",
                hint="Use the remove command 'rm'.",
                command="rm",
                syntax="rm old_trash.txt",
                explanation="Removes specified file permanently.",
                predicate_type="file_not_exists",
                predicate_target="old_trash.txt",
                xp_reward=30,
                hints=[
                    "The remove command is 'rm'.",
                    "Type: rm old_trash.txt",
                    "Type: rm old_trash.txt (or select option B)",
                ],
                scenario="Tidy up! Remove 'old_trash.txt' from the directory.",
                question="Which command deletes the unwanted file 'old_trash.txt'?",
                options=[
                    "del old_trash.txt     - Windows delete command",
                    "rm old_trash.txt      - Remove file in Linux",
                    "trash old_trash.txt   - Move to desktop trash",
                    "erase old_trash.txt   - Clear file blocks",
                ],
                correct_option="B",
            ),
        ],
        reward_item=Item(
            id="item_watering_can",
            name="Copper Watering Can 🪣",
            description="Keeping everything fresh, hydrated, and orderly.",
            category="tool",
            rarity="uncommon",
        ),
        reward_xp=100,
        environment_tree={
            "old_trash.txt": "Expired compost and dry leaves.\n",
        },
    )

    # -------------------------------------------------------------------------
    # LEVEL 9: WHO CAN OPEN THIS? (chmod)
    # -------------------------------------------------------------------------
    quests[8] = Quest(
        id="level_09",
        sector_id=8,
        sector_name="Who Can Open This?",
        npc_name="Nova",
        lore="Every file in Linux has permissions (read, write, execute) for the owner, group, and others.",
        dialogue=[
            "Hi! I'm Nova, guardian of file safety.",
            "A script named 'run_me.sh' is locked and cannot be executed.",
            "Use 'chmod' to grant execute permissions!",
        ],
        objectives=[
            Objective(
                id="obj_9_1",
                description="Set executable permissions on 'run_me.sh' (mode 755 or +x).",
                hint="Use 'chmod 755 run_me.sh' or 'chmod +x run_me.sh'.",
                command="chmod",
                syntax="chmod 755 run_me.sh",
                explanation="Modifies file access permissions.",
                predicate_type="permission_equals",
                predicate_target="run_me.sh",
                predicate_expected="755",
                xp_reward=100,
                hints=[
                    "In octal notation, 755 grants rwxr-xr-x.",
                    "Try: chmod 755 run_me.sh (or chmod +x run_me.sh)",
                    "Type: chmod 755 run_me.sh (or select option A)",
                ],
                scenario="The shell script 'run_me.sh' needs executable permissions.",
                question="Which command grants execute permissions to the script 'run_me.sh'?",
                options=[
                    "chmod 755 run_me.sh       - Set read, write, and execute permissions",
                    "chown root run_me.sh      - Change file owner",
                    "attrib +x run_me.sh       - Windows file attributes",
                    "cat run_me.sh             - Read script content",
                ],
                correct_option="A",
            ),
        ],
        reward_item=Item(
            id="item_silver_key",
            name="Silver Key 🗝️",
            description="Symbol of permission mastery and safe access.",
            category="key",
            rarity="rare",
        ),
        reward_xp=100,
        environment_tree={
            "run_me.sh": {
                "content": "#!/bin/sh\necho 'The script ran successfully! 🌱'\n",
                "permissions": "0644",
            },
        },
    )

    # -------------------------------------------------------------------------
    # LEVEL 10: COUNT & SORT (wc, sort)
    # -------------------------------------------------------------------------
    quests[9] = Quest(
        id="level_10",
        sector_id=9,
        sector_name="Count & Sort",
        npc_name="Penny",
        lore="Data is best when it's neat and orderly! Let's count entries and organize our lists.",
        dialogue=[
            "'wc -l' counts the number of lines in a file.",
            "'sort' puts lines in clean alphabetical order!",
        ],
        objectives=[
            Objective(
                id="obj_10_1",
                description="Count the total number of lines in 'guestbook.txt'.",
                hint="Use the word count command with the '-l' (lines) flag.",
                command="wc",
                syntax="wc -l guestbook.txt",
                explanation="Counts lines, words, and characters in a file.",
                predicate_type="pattern_matched",
                predicate_target="wc",
                predicate_expected="guestbook.txt",
                xp_reward=50,
                hints=[
                    "The word count tool is 'wc'.",
                    "Pass '-l' to count lines: wc -l guestbook.txt",
                    "Type: wc -l guestbook.txt (or select option B)",
                ],
                scenario="How many visitors signed our guestbook? Let's count.",
                question="Which command counts the number of lines in 'guestbook.txt'?",
                options=[
                    "count guestbook.txt     - Query word count",
                    "wc -l guestbook.txt      - Word count with line flag",
                    "lines guestbook.txt      - Print line indices",
                    "sort guestbook.txt       - Reorder entries",
                ],
                correct_option="B",
            ),
            Objective(
                id="obj_10_2",
                description="Sort the lines of 'friends.txt' in alphabetical order.",
                hint="Use the 'sort' command followed by the filename.",
                command="sort",
                syntax="sort friends.txt",
                explanation="Sorts lines in text files alphabetically.",
                predicate_type="pattern_matched",
                predicate_target="sort",
                predicate_expected="friends.txt",
                xp_reward=50,
                hints=[
                    "The sort command is 'sort'.",
                    "Try: sort friends.txt",
                    "Type: sort friends.txt (or select option B)",
                ],
                scenario="Our friends list is jumbled. Let's alphabetize it.",
                question="Which command sorts the lines of 'friends.txt' alphabetically?",
                options=[
                    "order friends.txt     - Arrange by date",
                    "sort friends.txt      - Sort lines in alphabetical order",
                    "cat -s friends.txt    - Squeeze blank lines",
                    "rank friends.txt      - Compute entry scores",
                ],
                correct_option="B",
            ),
        ],
        reward_item=Item(
            id="item_abacus",
            name="Polished Wooden Abacus 🧮",
            description="Calculates counts and lines with peaceful clicks.",
            category="tool",
            rarity="uncommon",
        ),
        reward_xp=100,
        environment_tree={
            "guestbook.txt": "Alice\nBob\nCharlie\nDiana\nEdward\n",
            "friends.txt": "Zoe\nBob\nCharlie\nAlice\n",
        },
    )

    # -------------------------------------------------------------------------
    # LEVEL 11: CONNECT THE COMMANDS (|)
    # -------------------------------------------------------------------------
    quests[10] = Quest(
        id="level_11",
        sector_id=10,
        sector_name="Connect the Commands",
        npc_name="Byte",
        lore="The pipe operator '|' connects commands together like LEGO bricks!",
        dialogue=[
            "In Linux, the output of one command can become the input of the next.",
            "Use '|' to chain 'cat' directly into 'sort'!",
        ],
        objectives=[
            Objective(
                id="obj_11_1",
                description="Pipe the output of 'cat inventory.txt' into 'sort'.",
                hint="Use the pipe character '|' between cat and sort.",
                command="cat,sort",
                syntax="cat inventory.txt | sort",
                explanation="Connects the stdout of one program to the stdin of another.",
                predicate_type="pipeline_used",
                predicate_target="sort",
                xp_reward=100,
                hints=[
                    "Write 'cat inventory.txt', then '|', then 'sort'.",
                    "Try: cat inventory.txt | sort",
                    "Type: cat inventory.txt | sort (or select option A)",
                ],
                scenario="Chain cat and sort together using a pipeline '|'.",
                question="Which command pipes the output of 'cat inventory.txt' directly into 'sort'?",
                options=[
                    "cat inventory.txt | sort     - Stream file into sort command",
                    "cat inventory.txt > sort     - Overwrite a file named sort",
                    "sort < inventory.txt | cat    - Reverse stream order",
                    "cat inventory.txt & sort     - Run commands in background",
                ],
                correct_option="A",
            ),
        ],
        reward_item=Item(
            id="item_brass_pipe",
            name="Brass Garden Pipe 🎺",
            description="Channels streams of data smoothly from one tool to another.",
            category="tool",
            rarity="rare",
        ),
        reward_xp=100,
        environment_tree={
            "inventory.txt": "Zucchini\nCarrot\nApple\nBeet\n",
        },
    )

    # -------------------------------------------------------------------------
    # LEVEL 12: REDIRECT IT (>, >>)
    # -------------------------------------------------------------------------
    quests[11] = Quest(
        id="level_12",
        sector_id=11,
        sector_name="Redirect It",
        npc_name="Fern",
        lore="Redirect operators let you send output into files instead of printing to screen.",
        dialogue=[
            "'>' creates or overwrites a file.",
            "'>>' appends new text to the end without erasing!",
        ],
        objectives=[
            Objective(
                id="obj_12_1",
                description="Write 'Sunny day' into 'journal.txt' using '>'.",
                hint='Use: echo "Sunny day" > journal.txt',
                command="echo",
                syntax='echo "Sunny day" > journal.txt',
                explanation="Redirects output to a file, overwriting existing contents.",
                predicate_type="file_contains",
                predicate_target="journal.txt",
                predicate_expected="Sunny day",
                xp_reward=50,
                hints=[
                    "Use echo with '>' and the file name.",
                    'Try: echo "Sunny day" > journal.txt',
                    'Type: echo "Sunny day" > journal.txt (or select option A)',
                ],
                scenario="Create your journal entry using output redirection '>'.",
                question="Which command writes 'Sunny day' into a new file named 'journal.txt'?",
                options=[
                    'echo "Sunny day" > journal.txt     - Redirect output into file (overwrite)',
                    'echo "Sunny day" >> journal.txt    - Append output to file',
                    'echo "Sunny day" < journal.txt     - Read file into echo',
                    'echo "Sunny day" | journal.txt     - Pipe echo into file',
                ],
                correct_option="A",
            ),
            Objective(
                id="obj_12_2",
                description="Append 'Gentle breeze' into 'journal.txt' using '>>'.",
                hint='Use: echo "Gentle breeze" >> journal.txt',
                command="echo",
                syntax='echo "Gentle breeze" >> journal.txt',
                explanation="Appends output to the end of a file without overwriting.",
                predicate_type="file_contains",
                predicate_target="journal.txt",
                predicate_expected="Gentle breeze",
                xp_reward=50,
                hints=[
                    "Use '>>' to append text to the file.",
                    'Try: echo "Gentle breeze" >> journal.txt',
                    'Type: echo "Gentle breeze" >> journal.txt (or select option B)',
                ],
                scenario="Add a second line to your journal without overwriting the first.",
                question="Which operator appends text to the end of 'journal.txt' without erasing it?",
                options=[
                    'echo "Gentle breeze" > journal.txt     - Overwrites existing content',
                    'echo "Gentle breeze" >> journal.txt    - Appends text to end of file',
                    'echo "Gentle breeze" + journal.txt     - Math addition syntax',
                    'cat "Gentle breeze" >> journal.txt     - Invalid cat arguments',
                ],
                correct_option="B",
            ),
        ],
        reward_item=Item(
            id="item_quill",
            name="Feather Quill & Ink 🪶",
            description="Writes thoughts and outputs cleanly into scrolls.",
            category="tool",
            rarity="rare",
        ),
        reward_xp=100,
        environment_tree={},
    )

    # -------------------------------------------------------------------------
    # LEVEL 13: SEARCH + PIPE (grep | wc)
    # -------------------------------------------------------------------------
    quests[12] = Quest(
        id="level_13",
        sector_id=12,
        sector_name="Search + Pipe",
        npc_name="Byte",
        lore="Let's combine what we learned! We can feed a file into standard input using '<'.",
        dialogue=[
            "The '<' operator feeds a file into a command's standard input.",
            "Let's see how '<' works with 'wc -l'!",
        ],
        objectives=[
            Objective(
                id="obj_13_1",
                description="Feed 'recipe.txt' into 'wc -l' using '<'.",
                hint="Use: wc -l < recipe.txt",
                command="wc",
                syntax="wc -l < recipe.txt",
                explanation="Redirects input from a file into a command.",
                predicate_type="pipeline_used",
                predicate_target="wc",
                xp_reward=100,
                hints=[
                    "Type 'wc -l', then '<', then 'recipe.txt'.",
                    "Try: wc -l < recipe.txt",
                    "Type: wc -l < recipe.txt (or select option A)",
                ],
                scenario="Feed the recipe into wc using input redirection '<'.",
                question="Which command feeds 'recipe.txt' into 'wc -l' using standard input redirection?",
                options=[
                    "wc -l < recipe.txt     - Redirect file into command standard input",
                    "wc -l > recipe.txt     - Overwrite recipe.txt with zero lines",
                    "cat < wc -l recipe     - Malformed command",
                    "read recipe.txt | wc   - Pipe variable into wc",
                ],
                correct_option="A",
            ),
        ],
        reward_item=Item(
            id="item_prism",
            name="Glass Prism 💎",
            description="Splits single streams of light into brilliant spectra.",
            category="curio",
            rarity="rare",
        ),
        reward_xp=100,
        environment_tree={
            "recipe.txt": "Flour\nSugar\nButter\nEggs\nVanilla\n",
        },
    )

    # -------------------------------------------------------------------------
    # LEVEL 14: THE BIG MESS (Multi-skill Tidy Up)
    # -------------------------------------------------------------------------
    quests[13] = Quest(
        id="level_14",
        sector_id=13,
        sector_name="The Big Mess",
        npc_name="Penny",
        lore="An old workshop needs a thorough tidy-up. Search notes, remove clutter, and inspect everything!",
        dialogue=[
            "Almost a Master Explorer! This level tests searching, deleting, and detailed listings.",
            "Take your time and clean up the workshop!",
        ],
        objectives=[
            Objective(
                id="obj_14_1",
                description="Count lines containing 'clue' in 'notes.txt' using a pipeline.",
                hint='Try: grep "clue" notes.txt | wc -l',
                command="grep,wc",
                syntax='grep "clue" notes.txt | wc -l',
                explanation="Finds matching lines and counts them with a pipeline.",
                predicate_type="pipeline_used",
                predicate_target="wc",
                xp_reward=35,
                hints=[
                    "Chain 'grep' with 'wc -l'.",
                    'Try: grep "clue" notes.txt | wc -l',
                    'Type: grep "clue" notes.txt | wc -l (or select option B)',
                ],
                scenario="Search notes for clues and count the occurrences.",
                question="Which pipeline searches 'notes.txt' for 'clue' and counts the matching lines?",
                options=[
                    'find notes.txt "clue" | wc      - Invalid find syntax',
                    'grep "clue" notes.txt | wc -l   - Grep matching lines then count them',
                    "cat notes.txt > wc -l            - Overwrite wc -l file",
                    'grep -c "clue" > notes.txt      - Overwrites notes.txt',
                ],
                correct_option="B",
            ),
            Objective(
                id="obj_14_2",
                description="Remove the unwanted directory 'weeds' using rm -r.",
                hint="Use 'rm -r weeds' to remove a folder and its contents.",
                command="rm",
                syntax="rm -r weeds",
                explanation="Recursively removes a directory.",
                predicate_type="file_not_exists",
                predicate_target="weeds",
                xp_reward=35,
                hints=[
                    "Pass the '-r' (recursive) flag to 'rm'.",
                    "Type: rm -r weeds",
                    "Type: rm -r weeds (or select option B)",
                ],
                scenario="Weeds have overgrown the corner. Remove the directory.",
                question="Which command removes the directory 'weeds' and all items inside it?",
                options=[
                    "rm weeds        - Fails because weeds is a directory",
                    "rm -r weeds     - Recursively remove directory and contents",
                    "rmdir weeds     - Fails if folder is not empty",
                    "del weeds/*     - Windows command syntax",
                ],
                correct_option="B",
            ),
            Objective(
                id="obj_14_3",
                description="Inspect the final cleaned folder in detail using ls -la.",
                hint="Type 'ls -la' to see permissions, sizes, and hidden files.",
                command="ls",
                syntax="ls -la",
                explanation="Lists full detailed directory contents including dotfiles.",
                predicate_type="pattern_matched",
                predicate_target="ls",
                predicate_expected="-la",
                xp_reward=30,
                hints=[
                    "Combine '-l' and '-a' flags.",
                    "Type: ls -la",
                    "Type: ls -la (or select option A)",
                ],
                scenario="Inspect the freshly cleaned directory with full details.",
                question="Which command shows a detailed long-format listing including hidden files?",
                options=[
                    "ls -la     - Long format listing showing all hidden files",
                    "ls -s      - Show size blocks only",
                    "dir /a     - Windows directory listing",
                    "tree -d    - Show directories only",
                ],
                correct_option="A",
            ),
        ],
        reward_item=Item(
            id="item_broom",
            name="Golden Hand Broom 🧹",
            description="Keeps any directory immaculately clean and organized.",
            category="tool",
            rarity="epic",
        ),
        reward_xp=150,
        environment_tree={
            "notes.txt": "clue 1: look under the stone\nclue 2: check the tree\nnormal line\n",
            "weeds": {
                "dandelion.txt": "Wild weed\n",
            },
        },
    )

    # -------------------------------------------------------------------------
    # LEVEL 15: THE FINAL CHALLENGE (Master Explorer)
    # -------------------------------------------------------------------------
    quests[14] = Quest(
        id="level_15",
        sector_id=14,
        sector_name="The Final Challenge",
        npc_name="Byte",
        lore="The ultimate exploration! Find the Golden Star in the maze and claim your Master Explorer badge!",
        dialogue=[
            "You have learned navigation, reading, permissions, searching, and pipelines!",
            "Solve the three final puzzles to claim the Golden Star and complete your adventure!",
        ],
        objectives=[
            Objective(
                id="obj_15_1",
                description="Find where 'star.txt' is hidden in the maze.",
                hint='Use: find . -name "star.txt"',
                command="find",
                syntax='find . -name "star.txt"',
                explanation="Searches the maze for the hidden star.",
                predicate_type="pattern_matched",
                predicate_target="find",
                predicate_expected="star.txt",
                xp_reward=50,
                hints=[
                    'Search for the file by name with find: find . -name "star.txt"',
                    'Type: find . -name "star.txt" (or select option B)',
                    'Type: find . -name "star.txt"',
                ],
                scenario="Find where 'star.txt' is hidden inside the maze.",
                question="Which command searches the entire maze to locate 'star.txt'?",
                options=[
                    "search star.txt                  - Search desktop database",
                    'find . -name "star.txt"          - Recursively search tree for filename',
                    "locate star.txt                  - Query pre-built locate db",
                    "cat star.txt                      - Read file in current directory",
                ],
                correct_option="B",
            ),
            Objective(
                id="obj_15_2",
                description="Read the message inside 'maze/hallway/room_a/star.txt'.",
                hint="Use: cat maze/hallway/room_a/star.txt",
                command="cat,less",
                syntax="cat maze/hallway/room_a/star.txt",
                explanation="Reads the message from the golden star.",
                predicate_type="file_read",
                predicate_target="maze/hallway/room_a/star.txt",
                xp_reward=50,
                hints=[
                    "Use 'cat' with the full path to the star file.",
                    "Type: cat maze/hallway/room_a/star.txt (or select option B)",
                    "Type: cat maze/hallway/room_a/star.txt",
                ],
                scenario="Read the message inscribed on the Golden Star.",
                question="Which command reads the message inside 'maze/hallway/room_a/star.txt'?",
                options=[
                    "open maze/hallway/room_a/star.txt   - Open in external window",
                    "cat maze/hallway/room_a/star.txt    - Print file contents to terminal",
                    "ls maze/hallway/room_a/star.txt     - List file path only",
                    "head -0 maze/hallway/star.txt       - Display 0 lines",
                ],
                correct_option="B",
            ),
            Objective(
                id="obj_15_3",
                description="Write 'I_LOVE_LINUX' into 'trophy.txt' to win the game!",
                hint='Use: echo "I_LOVE_LINUX" > trophy.txt',
                command="echo",
                syntax='echo "I_LOVE_LINUX" > trophy.txt',
                explanation="Writes your victory proclamation into the trophy file.",
                predicate_type="file_contains",
                predicate_target="trophy.txt",
                predicate_expected="I_LOVE_LINUX",
                xp_reward=150,
                hints=[
                    "Use 'echo \"I_LOVE_LINUX\" > trophy.txt'.",
                    "Make sure the text matches exactly: I_LOVE_LINUX",
                    'Type: echo "I_LOVE_LINUX" > trophy.txt (or select option A)',
                ],
                scenario="Claim your victory and complete the final challenge!",
                question="Which command writes 'I_LOVE_LINUX' into 'trophy.txt' to claim the trophy?",
                options=[
                    'echo "I_LOVE_LINUX" > trophy.txt      - Write exact message into trophy.txt',
                    'echo "I_LOVE_LINUX" >> trophy.txt     - Append text to file',
                    'write "I_LOVE_LINUX" trophy.txt      - Non-standard shell syntax',
                    'cat "I_LOVE_LINUX" > trophy.txt      - Cat expects filename, not string',
                ],
                correct_option="A",
            ),
        ],
        reward_item=Item(
            id="item_golden_star",
            name="Golden Linux Star ⭐",
            description="Awarded to true terminal adventurers who mastered all 15 levels!",
            category="artifact",
            rarity="mythic",
        ),
        reward_xp=250,
        environment_tree={
            "start_here.txt": (
                "Welcome to the Final Challenge! 🌟\n"
                "Step 1: Use 'find . -name \"star.txt\"' to locate where the Golden Star is.\n"
                "Step 2: Read what the star says!\n"
                "Step 3: Write 'I_LOVE_LINUX' into 'trophy.txt' using '>' to claim your trophy!\n"
            ),
            "maze": {
                "hallway": {
                    "room_a": {
                        "star.txt": "⭐ You found the Golden Star! Write 'I_LOVE_LINUX' into 'trophy.txt' to win!\n",
                    },
                },
            },
        },
    )

    return quests
