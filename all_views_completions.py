# Extends Sublime Text autocompletion to find matches in all open
# files. By default, Sublime only considers words from the current file.

import sublime_plugin
import sublime
import re


# limits to prevent bogging down the system
MAX_VIEWS = 20
MAX_WORDS_PER_VIEW = 100
MIN_WORD_SIZE = 3


class AllAutocomplete(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        words = []

        # Limit number of views but always include the active view. This
        # view goes first to prioritize matches close to cursor position.
        other_views = [v for v in sublime.active_window().views() if v.id != view.id]
        views = [view] + other_views
        views = views[0:MAX_VIEWS]

        for v in views:
            if len(locations) > 0 and v.id == view.id:
                view_words = v.extract_completions(prefix, locations[0])
            else:
                view_words = v.extract_completions(prefix)
            view_words = view_words[0:MAX_WORDS_PER_VIEW]
            view_words = fix_truncation(v, view_words)
            words += view_words

        words = without_duplicates(words)
        matches = [(w, w) for w in words]
        return matches


# keeps first instance of every word and retains the original order
# (n^2 but should not be a problem as len(words) <= MAX_VIEWS*MAX_WORDS_PER_VIEW)
def without_duplicates(words):
    result = []
    for w in words:
        if w not in result:
            result.append(w)
    return result


# Ugly workaround for truncation bug in Sublime when using view.extract_completions()
# in some types of files.
def fix_truncation(view, words):
    fixed_words = []
    words_to_fix = []
    for w in words:
        if len(w) >= MIN_WORD_SIZE:
            words_to_fix.append(w)
        else:
            fixed_words.append(w)

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
                fixed_words += extended_words
            else:
                # to compensate for the missing match problem mentioned above, just
                # use the old word if we didn't find any extended matches
                fixed_words.append(w)
        else:
            #Pass through non-truncated words
            fixed_words.append(w)
    return fixed_words
