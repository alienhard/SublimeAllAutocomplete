# Extends Sublime Text autocompletion to find matches in all open
# files. By default, Sublime only considers words from the current file.

import sublime_plugin
import sublime
import re
import time
from os.path import basename


MAX_VIEWS = 20
MAX_WORDS_PER_VIEW = 100
MAX_FIX_TIME_SECS_PER_VIEW = 0.01


def plugin_loaded():
    global settings
    settings = sublime.load_settings('All Autocomplete.sublime-settings')


class AllAutocomplete(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        if is_excluded(view.scope_name(locations[0]), settings.get("exclude_from_completion", [])):
            return []

        words = []

        # Limit number of views but always include the active view. This
        # view goes first to prioritize matches close to cursor position.
        other_views = [
            v
            for v in sublime.active_window().views()
            if v.id != view.id and not is_excluded(v.scope_name(0), settings.get("exclude_sources", []))
        ]

        for v in [view, *other_views][0:MAX_VIEWS]:
            if len(locations) > 0 and v.id == view.id:
                view_words = v.extract_completions(prefix, locations[0])
            else:
                view_words = v.extract_completions(prefix)
            view_words = filter_words(view_words)
            view_words = fix_truncation(v, view_words)
            words += [(w, v) for w in view_words]

        words = without_duplicates(words)

        matches = []
        for w, v in words:
            trigger = w
            contents = w.replace('$', '\\$')
            if v.id != view.id and v.file_name():
                trigger += '\t(%s)' % basename(v.file_name())
            if v.id == view.id:
                trigger += '\tabc'
            matches.append((trigger, contents))
        return matches


def is_excluded(scope, excluded_scopes):
    for excluded_scope in excluded_scopes:
        if excluded_scope in scope:
            return True
    return False


def filter_words(words):
    MIN_WORD_SIZE = settings.get("min_word_size", 3)
    MAX_WORD_SIZE = settings.get("max_word_size", 50)
    return [w for w in words if MIN_WORD_SIZE <= len(w) <= MAX_WORD_SIZE][0:MAX_WORDS_PER_VIEW]


# keeps first instance of every word and retains the original order, O(n)
def without_duplicates(words):
    result = []
    used_words = set()
    for w, v in words:
        if w not in used_words:
            used_words.add(w)
            result.append((w, v))
    return result


# Ugly workaround for truncation bug in Sublime when using view.extract_completions()
# in some types of files.
def fix_truncation(view, words):
    fixed_words = []
    start_time = time.time()

    for i, w in enumerate(words):
        #The word is truncated if and only if it cannot be found with a word boundary before and after

        # this fails to match strings with trailing non-alpha chars, like
        # 'foo?' or 'bar!', which are common for instance in Ruby.
        match = view.find(r'\b' + re.escape(w) + r'\b', 0)
        truncated = is_empty_match(match)
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

        # if too much time is spent in here, bail out,
        # and don't bother fixing the remaining words
        if time.time() - start_time > MAX_FIX_TIME_SECS_PER_VIEW:
            return fixed_words + words[i+1:]

    return fixed_words


if sublime.version() >= '3000':
    def is_empty_match(match):
        return match.empty()
else:
    plugin_loaded()
    def is_empty_match(match):
        return match is None
