# General Design


# SQL Table Notes


## Design

### Tags

* autoincrement primary key
  - autoincrement to prevent reuse of `rowids` when freed up ... which might be valuable for data integrity over the lifetime of the database, 
  - though it apparently takes up more CPU, addition of tags won't be common, so it shouldn't be a problem
* long form (tag + parent_id)
* Use recursive queries to get full parent path
* Ensure uniqueness across tag name and parent_id
  - See [SQLite Docs](https://www.sqlite.org/lang_createtable.html#uniqueconst)
  - See on conflict response: https://www.sqlite.org/lang_conflict.html
  - To get uniqueness for root tags is tricky, as NULL is always unique!
    + Need additional check
* Use trigger to automatically create full parent string for each tag
  - uses large recursive query ... could join full parent string on to tags table
    + Main purpose of this is to have a good mapping between the unique tag and a textual representation of the tag
  - As adding and removing tags will be relatively infrequent, _automatically_ deriving full parent paths should be fine.
* **Architecture**
  - ?? Initialise tags table with a single tag: `root` with parent `NULL` ??.
  - `root` is the parent of all top level tags (and so used as the filter for top level tags)
  - Create trigger on `update`, `delete` and `insert` (on tags table)
    + trigger runs:
      * `delete` to clear the `full_tag_paths` table
      * `insert` on the table `full_tag_paths` using the recursive query



#### Full parent derivation

```sql
with recursive tags_parents(id, tag, parent_id, parent) as
    (
    select a.id, a.tag, a.parent_id, b.tag as parent
    from tags a
    left join tags b
    on a.parent_id = b.id
    ),
pnts(id, tag, parent_id, id_path, tag_path) as
    (
    select
        id, tag, parent_id,
        ifnull(parent_id, '-') as id_path, ifnull(parent, '-') as tag_path
    from tags_parents
    where parent_id is NULL
    union
    select
        m.id, m.tag, m.parent_id,
        ifnull(pnts.id_path, '-') || '/' || pnts.id as id_path,
        ifnull(pnts.tag_path, '-') || '/' || pnts.tag as tag_path
    from tags_parents m
    join pnts
    on pnts.id = m.parent_id
    order by m.parent_id desc
    )
select
    id, tag, parent_id,
    id_path || '/' || id as full_path,
    tag_path || '/' || tag as full_tag_path
from pnts
```


#### Note Writing

* Tags will be added to notes through YAML frontmatter
* Comma separated tags so that can have multiple tags
* Written as a full path (eg `python/std_lib/datetime`)

* **Note -> database**
  - tag path matched against `full_tag_paths`, which provides the actual tag id that relates directly back to the `tags` table.
  - `note_tags` table updated with note id and tag id
* **database -> Note**
  - Search for a substring in all tag paths, and select manually
  - eg: `[tag_path for tag_path in full_tag_paths if "query" in tag_path]`
* **New tag -> database**
  - Select parent (incl `null` for root level tag) from full_tag_paths then append new child
  - Can do directly by parsing text directly:
    + _presume full path!_
    + find _longest_ already existing path in new path, _that starts at 0 in new path_
      * What if no match?  Then every tag is new, and first is at root level ... handle in the adding stage
    + get id of parent_path.  _If not present_, then parent_path is null
    + Split remainder of new_path into tags
    + For each new tag, add with previous parent as parent


### Files

* Files stored fully with FTS
  - FTS on top of actual storage in a separate source table: https://kimsereylam.com/sqlite/2020/03/06/full-text-search-with-sqlite.html, https://www.sqlite.org/fts5.html#external_content_tables
    + Use triggers to automatically update the FTS from the base table: https://sqlite.org/lang_createtrigger.html
  - Use YAML metadata for title, tags
  - store metadata in the database separately from the body
  - Store latest update date to compare with changes on disk
  - store mod time as a string of timestamp ... to rely entirely on python datetimes
  - store id as int of timestamp ... only second resolution, but YAGNI for greater resolution (for now) ... maybe increase later or if not unique, wait?

* References
  - Bibliographical citations can be added freely to any note.
  - To be more structured ... each source can get it's own note, and possibly tagged as a "source" (bigger topic of what to use tags for).  Citing a source is a link to a source note, which can also contain a general summary about the source content if desired.

### Links

* Stay as close to markdown syntax as possible:
  - _eg_ [My first link](/20201016154437)

```
Here is a zettelkasten link: [My First Link](/20201016154437)
```

* Title of the note is the link title
  - This need not match the note's actual title, as it is not static.
  - The link title can be just for convenience within the context of the note
  - For making new notes from links, through some hotkey, whatever title is provided will have to be used for the actual title of the newly created note.
    + The newly created id will have to be inserted automatically
* The URL is a forward slash (`/`) followed by the unique ID
* This should have the following qualities:
  - Fit's into ordinary markdown
  - Easily detectably distinct from ordinary links
  - Expressive
  
#### Regex

```regex
\[[\w ]*\]\(\/\d{12,14}\)
```


Or, alternatively, to allow for any characters in the title:

```regex
\[.*\]\(\/\d{12,14}\)
```

* If/when creating a new note with such syntax, the title will have to be checked to be only ASCII
  - pretty easy in python


#### Managing new links to potentially new notes

* While writing a note, two hurdles might occur
  - Inserting a link by the id is difficult as the ID is hard to remember
  - Inserting a link to a note you haven't created yet but want to.
  
* For the first problem, the only two alternatives are:
  - Parse links with titles only and match the written title against the database.  Sounds good and easy, as titles are easier to remember, but in practice it will go wrong frequently I imagine
  - Use an automated process (through a text editor for instance) for searching for notes and inserting appropriate links
    + Would be good to ensure that this facility is not bound to any text editor and can be run through a CLI or web API

* For the second problem, the two solutions are similar in nature to those above:
  - Parse for links that lack an ID (_but have a title!_), and create those new notes when the note is parsed (perhaps optionally so)
    + **I Actually like this.**  It can be a clean fallback which can be run at all times in the process of parsing notes.  Parse for `new_links`, create new notes, go back and replace new links with actual links (with ids).  **Kinda a nice to have at this pint though.**
  - A quick automated process for creating a new note from some easily selectable text (again, inside a text editor but should not be bound to the text editor's API)

### Front Matter

* Written in YAML (ie, YAML front matter)
* Pretty easy to manually parse
* Fields:
  - title
  - tags
  - _extendable in the future?_ ... really depends on the parsing


```markdown
---
title: Python
tags: tech
---

## Content Body

This is a link: [Link](/20201016154437)
```


#### Regex

```regex
(?s)^---.*---
```

* `(?s)` Sets the _dot matches newlines_ flag (ordinarily `re.S`).



## Querying

* FTS on title
* FTS on text
* shallow and deep Children of note
* shallow parents of note
* shallow and deep notes of particular tag
  - deep means to include all tags that are children of target
  - unsure exactly how to do this with current scheme:
    + http://howto.philippkeller.com/2005/04/24/Tags-Database-schemas/
    + https://stackoverflow.com/questions/20856/recommended-sql-database-design-for-tags-or-tagging
  - 
* Combine tag queries with rest of above
  - This ... could be non-trivial ... especially with the FTS ...
  - How combine complex queries with FTS queries?  Sub queries and joins?
  - How use tags with other queries?  _may want to rethink the tags model ... depends on performance at scale really_
    + 
    + instead, could leverage FTS and have a tags column with comma separated tags (including tag paths with slashes: `parent_tag/child_tag`) (using either FTS or `LIKE` matching: https://sqlite.org/lang_expr.html#the_like_glob_regexp_and_match_operators)
      * insertion of tag strings could by managed by python, checking the existing tag tables and parent joins, and inserting as appropriate.  But then updating and deleting notes and/or tags could get very tricky.
    + Instead ... could flip the process:
      * Keep current model, but add ...
      * first, table of all unique combinations of tags
      * second, Assign to each note a single tag id in a single column in the notes table
      * Adding a tag to a note, adds the unique combination if it does not exist, then add this id to the note
        - _But ... how have unique combinations of arbitrary length?_
      * 

## Config

* Use python files (**why not!**)
  - **Actually, probably better to use `INI` files** as supported by the [standard library](https://docs.python.org/3/library/configparser.html)
* Use python import machinery to load an arbitrary file (see code below)
* Have up to three locations for a config file:
  - Package default file loaded as the fallback
  - Home directory
  - Current working directory (??)
    + not sure worth it
    + Idea would be to have locally independent working spaces defined by local config files
* Options
  - zk_path: path of database/filebase (`zekellbase`)
  - alt_paths: support multiple zekellbases (_nice to have really!_)
    + paths and names
    + currently selected zekellbase for all commands to run against

### Example Code

```python
import importlib
import importlib.machinery
import importlib.util

# provide absolute path of config
loader = importlib.machinery.SourceFileLoader(
    'test', '/Users/errollloyd/Developer/zekell/.zekell_config')
spec = importlib.util.spec_from_loader(loader.name, loader)
mod = importlib.util.module_from_spec(spec)
loader.exec_module(mod)
# mod.VARIABLE
```

## Cleaning

* To ensure consistency between the file-base and the database, a few batch functions will probably be necessary at some point
  - Check all notes in the database correspond to all files in the file-base
  - Add all files note in the database
  - Remove all files not in the database

## Updating Links

* To update links:
  - driven by notes, and therefore from files (_for now_).
  - do a full refresh of all links from note:
    + delete all with current note as parent
    + add links in current note
  - _update `db.ex()` function_ to allow batch statements so that the initial removal is rolled back should anything go wrong with the insert

## Updating Tags

* To update note_tags:
  - same as for links
* To update tags:
  - _Tricky!_
  - this is to update the _names_ or even the _parent(s)_ of the tags which are already assigned to a note.
    + For tags not assigned to a note, essentially a simple update
  - to change the name of a tag would require updating the text of every note, _reliably_.
    + update the tag column in tags
    + using regular expressions `re.sub()`, iterate through every note with specific tag in note_tags, find tag in frontmatter, and replace with new tag.
    + As the ids of the tag and notes stay the same, nothing else needs to be changed
  - to change the parent tag of a tag (ie, to move to a new parent)
    + it means whole path will change
    + old parent will stay in tact (removal of that would be another process)
    + create new tag under desired parent
    + as above, go through all necessary notes to change the note path of the original tag text in the frontmatter
  - To change any/all component of a tag's path
    + chain the processes above together essentially
    + create new tag as one would create a new tag path
    + iterate through all old notes and substitute old text with new
  - **The central challenge is relaibly substituting the old text in the frontmatter with the new tag path**
    + Engineering the regular expression will be important but doable
    + enabling a note backup and rollback process is probably a good idea.
  

## Deleting Tags

* Simple remove, conditional on whether any rows in `note_tags` containing the tag
  - Perhaps a fancy function at some point that will automatically remove such tags from the text of notes


# Tasks

- [X] Move all creation SQL code to `schema.sql`
- [X] Adjust tests accordingly:
- [X] Create files with FTS
- [X] Create references table
- [X] create note-tags table
- [X] create tags hierarchy auto-make trigger
- [X] make trigger occur on insert, update and delete
- [X] write tests for full_path_tags triggers
- [X] Parse files for metadata
  - [X] Add to table
  - [X] Include update and delete functionality 
- [X] Add to files/notes table
- [X] **Sort out SQL commit and close workflow!!**
  * Just commit on all calls to `ex()`?
    - *Yea ... this ... already done with context manager*
  * Or, something more sophisticated?
- [X] add to note_tags table
- [X] Use proper updating code for tags and links
  - [X] Add batch statements in db.ex()
  - [X] Update links instead of merely adding
  - [X] update note_tags instead of merely adding
- [X] Enable adding whole note from scratch
- [ ] Enable configuration for locating database etc
- [ ] Utility function for batch update of database from notes
  - [X] add file to database
  - [X] batch add multiple files to database (taking care of linking issues)
  - [ ] find all files ahead of database (using mod time and os modtime?)
  - [ ] batch add all files ahead of database
* [ ] Delete notes
  * [ ] Remove links
* [ ] Change note title
  * Because of the binding between note files and notes in the database, this may not be trivial
    - `update_note()` works by updating all fields for the record with the provided note id.  So, for this function, relying on a constant note_id is viable, *so long as a valid file path is provided with the current version of the note, even with a changed title*.
    - The CLI `update` relies on the note_id to then retrieve the title of the note from which the path of the file is *inferred*.  This is quick and convenient.  But, to change the title of a note, a distinct function will be required.
      + takes note_id (fuzzy too)
      + obtains full note_id from database along with older title
      + Searches for note_file with matching note_id
        * If can't be found, error
      + performs update using path of actual note file found in search
    - [X] Update `cli_update` to search for matching notes (by note_id) when the file_path title has changed
    - [ ] When using the package and not the CLI for the sublime plugin, clean the process up by updating directly with the file's current path and name using the `update_note()` function, checking if the id exists etc.
    - Updating a note, which is done by starting with the file, will hit an error if the title has been changed (even though the id is unchanged).
+ [ ] Delete Tags
  * Only if not used in any notes!
- [ ] add to references table
- [ ] create assets and asset links tables
- [ ] Look into adding indices for columns likely to be used heavily in queries
  * Eg, parent and child note ids in `note_links`.
  * See [sqlite docs on query planning and indices](https://www.sqlite.org/queryplanner.html)
  * Whereever `UNIQUE` constraints are applied an index is effectively created (see [docs on create table](https://www.sqlite.org/lang_createtable.html#unique_constraints)).
    - So ... **only the `note_tags` table would need an index**... or unique constraint on both columns
    
* [X] Add unique constraint or an index on `note_tags`
  * Makes sense to ensure uniqueness here
  * Should create an index that should make queries faster
  * **Perhaps unnecessary**
    - Using `explain query plan` shows lines like `SEARCH TABLE note_tags AS c USING AUTOMATIC COVERING INDEX (tag_id=? AND note_id=?)`, indicating that an index is created automatically already.  This is probably through the foreign key constraint that references the id columns of the `notes` and `tags` tables, both of which are primary key columns (and so should be indexed)
    - Though see the [sqlite docs on foreign keys](https://sqlite.org/foreignkeys.html#fk_indexes) where it is suggested an index on the child columns is still useful for when certain actions such as delete occur.

* [X] Create CLI
  * General a CRUD interface on notes and tags + querying
  * [X] Add sql command for straight sql
  * [X] add custom query command for custom short hand queries
  * [X] Add update specific note/file command
- [X] Wrap functionality around note staging (mostly CLI)
  * Stage note when opened through CLI so that can be readily updated once edited by external app
  * List all staged notes
  * Batch update all staged notes
    - Check ones have actually been updated?? (too much effort really)
  * mainly for editing notes purely through CLI

* [ ] Can update `full tag path` triggers to use a single CTE?
 * write the CTE once, and refer back to it in each trigger _!!?_
* [ ] Create query functions/API
  * [X] Create a super master query that automatically joins multiple optional queries together
    * Maybe use multiple CTEs for each component, then join them all together at the end on a commonly named `note_ids` column (??)
    * In combining the components of this query, there will be active and passive filtering
      - Eg: all notes that are children of note X, or all notes that are children of the notes from the previous component ... how to string all of this together?  _best approach is probably to put together various specific queries that are obviously useful, to get a feel for how it can all be put together_
      - Well, _passive_ filtering is done just by joining (kinda easy).  Ordinarily, active filtering would involve a `WHERE` within a subquery or CTE.
  * [X] Allow for simple _children of_ and _parents of_ passive components
  * [ ] Modify the `title` and `body` components to always be one CTE
    * At the moment, they are separate and are joined.
    * **for some reason**, this is a sub-optimal join, performing worse than other queries by orders of magnitude.
    * But, if both `where` statements are put into a single CTE, performance is excellent again.
    * Have some code that looks for both `title` and `body` and constructs a single CTE
    * To combine them requires only a single `where` statement:
      - `where title match "alice" and body match "queen"`
      - more fully ... 

```sql
with
title_notes(note_id) as (
    select rowid from notes_fts
    where title match "alice" and body match "queen"
)
select z.id,z.title
from title_notes a
inner join notes z on a.note_id = z.id
```


  * [ ] Allow for OR between components (using `outer join` rather than `inner join`)
    * sqlite doesn't support full outer joins.  They can be hacked together with a union of mirroring left joins ... but would it be worth it?
  * [ ] Allow for complex tag queries
    - boolean operations on multiple tags
    - **Perhaps the [toxi](http://howto.philippkeller.com/2005/04/24/Tags-Database-schemas/) scheme is not appropriate for this?**  It's possible, but perhaps to combersome especially if trying to integrate it with other query components.
    - Maybe just using FTS, with a single `tags` column, with space separated tags and slashes (`/`) for hierarchy, would work better for querying?
      + Harder to query _what are all the tags in the database_ then ... so maybe both?
      + To remove the slash (`/`) from token separators see [docs on unicode tokenizer options](https://www.sqlite.org/fts5.html#unicode61_tokenizer) where characters can be added to the set of token and separator characters.  With this, whitespace would be used to separate tags and slashes would be retained as part of a single token.
      + Boolean queries would become simpler, using `sql` booleans on `like "%TAG%"` statements (see [examples in this blog post](http://howto.philippkeller.com/2005/04/24/Tags-Database-schemas/))
    - Including tag children in query (ie, tag `software` includes `software/theory`)
      + Probably best as a separate action from direct tag search ... simple recursive?
        + first step is to find all tags that are child of specified tag
        + Then, a simple `where tag_id in (...)` should do it.

```sql
-- All children of tag with parent_id ? 
    with recursive all_tag_children(id, tag, parent_id) as (
        -- Optionally including the initial tag too
        select id, tag, parent_id from tags
        where id = ?
        union
        select id, tag, parent_id from tags
        where parent_id = ?
        union
        select a.id id, a.tag tag, a.parent_id parent_id
        from tags a
        inner join all_tag_children b on a.parent_id = b.id
    ),
    tag_children_notes(note_id) as (
        select note_id from note_tags
        where tag_id in (
            select id from all_tag_children
        )
    )
    -- End of CTE
    -- selection in the course of full query
    select note_id from tag_children_notes

```

  * [X] Add follow-through children (and parent) query commands that select all immediate children of the previously selected notes
  * [X] Same for parent (?)
  * [ ] Add a distinct or group by to eliminate duplicates in children or parents
    * from inspections of query plans (with `explain query plan`), distinct or group by make no difference in the plan.  Quick timing tests show no observable difference in the timing.

```sql
-- For example

-- Previous selection ... simple title FTS
with title_notes(note_id) as (
    select rowid from notes_fts where title match "alice"
)
,
-- Actual children notes CTE
-- note that both parent and child note ids are required
-- here child_note_id is aliased to note_id as it will continue along in the chain of joins
children_notes(parent_note_id, note_id) as (
    select parent_note_id, child_note_id
    from note_links
)
-- selecting and joining
select z.id
from title_notes a
-- This is different from the usual pattern, where the join MUST be on the parent_note_id column
-- whilst the child_note_id continues along as note_id
-- to implement programmatically will require some logic to alter the usual pattern for
-- these "passive" "follow-through" CTEs
inner join children_notes b
    on a.note_id = b.parent_note_id
inner join notes z
    on b.note_id = z.id
```

  * [ ] Querying all children (at all levels) of a note (or even set of notes)
    * [ ] Need a recursive CTE
      * Can limit the number of levels?  Could be useful to do so only to 5 levels or so so that the number of notes doesn't explode?
      * How handle cycles?
        - Not sure can limit number of cycles, _but only total number of rows added_ through an ordinar `LIMIT` statement

```sql
-- Note the limit of 100 in final line
-- This is arbitrary, but a good safety limit makes sense (maybe 1000?)
-- Also note that this requires the seed parent_note_id
  -- Could use a like %XXXX fuzzy search for the note_id ?
with recursive all_children(parent_id, note_id) as (
    select parent_note_id, child_note_id from note_links
    where parent_note_id = ?
    union
    select parent_note_id, child_note_id 
        from note_links a
        inner join all_children b
        on b.note_id = a.parent_note_id
        limit 100
)
select note_id from all_children
```



  * [ ] ensure custom query interface is protected from sql insertion attacks


* [X] Run performance tests for various numbers of notes
  * 1000, 5000, 10_000, 50_000, 100_000
  * Use instance on AWS
  * need code for:
    - making dummy notes (like from alice in wonderland)
    - running and timing queries
      + Probably just use `zekell` CLI with `q` search machinery.
    - Setting up and tearing down notes


* [X] Allow for fuzzy search over note ids??
  * Idea is to be like git SHAs ... allow using the first 6 digits of a note to search for a ntoe
  * 6 digits is pretty easy for short term memory ... essentially Hour:Minute:second, and will most likely be unique or close to
    - 12 hours (working time) * 60 minutes * 60 seconds ~ 40_000
  * Probably create another FTS column for the row id?
  * Actually, this works already with basic `like %TOKEN%` syntax **!!!**:
  
  ```sql
  select id from notes where id like "%83006%"
  -- returns (20211031083006)
  ```

* [ ] Add run_log for all tables for version control and viable sync options
* [ ] Having running `last_mod_time` for whole database
  * update with triggers or use python?  (_probably triggers!_)
  * Could maybe just use the run_log?  _Probably not efficient!_
    - _Generally philosophy with this database is make reading fast and writing slow (indices, unique constraints, triggers, etc)._

* [ ] Create a web API interface
  * could become primary means of interaction
    - run always in background
    - allow for WAL and multiple connections, which requires another pragma ([see documentation](https://www.sqlite.org/wal.html))
    - requires either hacking the stdlib (too much) or using bottle (minimal)

* [X] Change modified time column to float (?)
  * Idea is to enable easier sorting in the database?
  * but sqlite seems quite happy to sort text.  In fact, it seems faster compared to sorting floats, which makes some sense as floating point might introduce some problems. ... **Note done, left as text!!**

* [ ] sublime plugin?
  * [ ] General Query interface:
    * Use plane text input (simple, but prone to errors) ... _or_ ...
    * Use [List Inputs](https://www.sublimetext.com/docs/api_reference.html#sublime_plugin.ListInputHandler) in combination with `next_inputs`
      - Initial selection are available keys (`tag`, `title` etc)
      - On selection, another list input (for `tag` for instance, where there are limited options), or, a general text input.
        + For `id`, a follow-up list input might make sense, which returns the list of possible options if there are more than one (or even when there is only one, just to confirm)


