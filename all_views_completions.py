# Extend Sublime Text 2 autocompletion to find matches in all open
# files of the current window. By default, Sublime only considers
# words from the current file.

import sublime_plugin
import sublime
import re


# limits to prevent bogging down the system
MAX_VIEWS = 25
MAX_WORDS = 10
MIN_WORD_SIZE = 3


class AllAutocomplete(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        words = set()
        views = [v for v in sublime.active_window().views()]

        # limit number of views but include the current view
        views = set(views[0:MAX_VIEWS])
        views.add(view)

        for v in views:
            view_words = v.extract_completions(prefix)
            view_words = view_words[0:MAX_WORDS]
            view_words = fix_truncation(v, view_words)
            words.update(view_words)
        matches = [(w, w) for w in words]
        return matches


# Ugly workaround for truncation bug in Sublime when using view.extract_completions()
# in some types of files.
def fix_truncation(view, words):
    fixed_words = set()
    words_to_fix = set()
    for w in words:
        if len(w) >= MIN_WORD_SIZE:
            words_to_fix.add(w)
        else:
            fixed_words.add(w)

    for w in words_to_fix:
        #The word is truncated if and only if it cannot be found with a word boundary before and after

        # this fails to match strings with trailing non-alpha chars, like
        # 'foo?' or 'bar!', which are common for instance in Ruby.
        truncated = view.find(r'\b' + re.escape(w) + r'\b', 0) is None
        if truncated:
            #Truncation is always by a single character, so we extend the word by one word character before a word boundary
            extended_words = []
            view.find_all(r'\b' + re.escape(w) + r'\w\b', 0, "$0", extended_words)
            if len(extended_words) > 0:
                fixed_words.update(extended_words)
            else:
                # to compensate for the missing match problem mentioned above, just
                # use the old word if we didn't find any extended matches
                fixed_words.add(w)
        else:
            #Pass through non-truncated words
            fixed_words.add(w)
    return fixed_words
