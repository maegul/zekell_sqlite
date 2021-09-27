pragma foreign_keys = ON;

-- > Notes

create table if not exists
notes (
    id integer primary key,
    title text,
    metadata text,
    body text,
    mod_time text
);

create virtual table if not exists
notes_fts using fts5(
    title,
    body,
    content='notes',
    content_rowid='id'
);

-- >> FTS Sync Triggers

create trigger if not exists
notes_ai
after insert on notes
begin
    insert into notes_fts (rowid, title, body)
        values (new.id, new.title, new.body);
end;

create trigger if not exists
notes_ad
after delete on notes
begin
    insert into notes_fts(notes_fts, rowid, title, body)
        values('delete', old.id, old.title, old.body);
end;

create trigger if not exists
notes_au
after update on notes
begin
    insert into notes_fts(notes_fts, rowid, title, body)
        values('delete', old.id, old.title, old.body);
    insert into notes_fts (rowid, title, body)
        values (new.id, new.title, new.body);
end;


-- > Note Links

create table if not exists
note_links (
    id interger primary key,
    parent_note_id integer,
    child_note_id integer,
    foreign key (parent_note_id)
        references notes (id),
    foreign key (child_note_id)
        references notes (id)
);


-- > Tags Table

create table if not exists
tags (
    id integer primary key autoincrement,
    tag text,
    parent_id text,
    foreign key (parent_id) references tags (id),
    unique (
        tag, parent_id
        )
    on conflict abort
);

-- >> Full Paths Table

create table full_tag_paths as
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
    id, tag,
    id_path || '/' || id as full_path,
    tag_path || '/' || tag as full_tag_path
from pnts;


-- >>> Update on insert
-- need to repeat for delete and update ...

create trigger if not exists tag_path_update
    after insert on tags
    begin
        delete from full_tag_paths;
        insert into full_tag_paths
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
                    id as id, tag as tag,
                    id_path || '/' || id as full_path,
                    tag_path || '/' || tag as full_tag_path
                from pnts;
    end;



create table if not exists
    note_tags (
        note_id integer,
        tag_id integer,
        foreign key (note_id) references notes (id),
        foreign key (tag_id) references tags (id)
        );




