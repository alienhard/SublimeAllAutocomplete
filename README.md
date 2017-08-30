All Autocomplete Sublime Text
===========================================================

Extends the default autocomplete to find matches in all open files.

By default Sublime only considers words found in the current file.


Install
-------

If you have Package Control installed in Sublime just press ctrl+shift+p (Windows, Linux) or cmd+shift+p (OS X) to open the Command Pallete.
Start typing 'install' to select 'Package Control: Install Package', then search for AllAutocomplete and select it. That's it.

You can also install this package manually by entering the Packages directory of Sublime Text 2/3 and issuing on a terminal:

    git clone https://github.com/alienhard/SublimeAllAutocomplete


Settings
--------

You can disable the additional autocompletion provided by this package for specific source files and even select syntax within files. In the Sublime menu go to Preferences > Package Settings > All Autocomplete > Settings – User.

Example: the following Setting would disable All Autocomplete for CSS and JavaScript code:

```
"exclude_from_completion": [
	"css",
	"js"
]
```

The names provided in this list are matched against the so-called "syntax scope" of the currently autocompleted input. For example, in a CSS file, when you start typing a new CSS class name, the syntax scope is "source.css meta.selector.css". The names you provide in the config above are partially matched against this scope. This means, you can completely disable All Autocomplete for all CSS code by specifying "css" – or you can disable it only for specific parts, for example, CSS selectors by specifying "selector.css". Or to disable completion in comments, include "comment" in the list.

Note, if you want to disable it in C source, but not in CSS, add "source.c" in the list (since "c" alone would also match css).

You can find the syntax scope of code at the current cursor position with Control+Shift+P.


LICENSE
-------

DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
Version 2, December 2004

Copyright (C) 2013 Adrian Lienhard <adrian.lienhard@gmail.com>

Everyone is permitted to copy and distribute verbatim or modified
copies of this license document, and changing it is allowed as long
as the name is changed.

DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

0. You just DO WHAT THE FUCK YOU WANT TO.