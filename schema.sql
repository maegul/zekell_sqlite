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




