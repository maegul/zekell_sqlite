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
  - See https://www.sqlite.org/lang_createtable.html#uniqueconst
  - See on conflict response: https://www.sqlite.org/lang_conflict.html
  - To get uniqueness for root tags is tricky, as NULL is always unique!
    + Need additional check
* Use trigger to automatically create full parent string for each tag
  - uses large recursive query ... could join full parent string on to tags table
    + Main purpose of this is to have a good mapping between the unique tag and a textual representation of the tag
  - As adding and removing tags will be relatively infrequent, automatically deriving full parent paths should be fine.
* **Architecture**
  - Initialise tags table with a single tag: `root` with parent `NULL`.
  - `root` is the parent of all top level tags (and so used as the filter for top level tags)
  - Create trigger on `update`, `delete` and `insert` (on tags table)
    + trigger runs:
      * `delete` to clear the `full_tag_paths` table
      * `insert` on the table `full_tag_paths` using the recursive query


_Full parent derivation_

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

# Tasks

- [X] Move all creation SQL code to `schema.sql`
- [X] Adjust tests accordingly:
- [X] Create files with FTS
- [X] Create references table
- [X] create note-tags table
- [X] create tags hierarchy auto-make trigger
- [ ] make trigger occur on insert, update and delete
- [ ] create assets and asset links tables
- [ ] Add to files/notes table
- [ ] add to references table
- [ ] add to note_tags table
- [ ] Parse files for metadata
  - [ ] Add to table
  - [ ] Include update and delete functionality 


