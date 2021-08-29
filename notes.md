# General Design


# SQL Table Notes

## Tags

### Design

* autoincrement primary key
* long form (tag + parent_id)
* Use recursive queries to get full parent path
* Ensure uniqueness across tag name and parent_id
  - See https://www.sqlite.org/lang_createtable.html#uniqueconst
  - See on conflict response: https://www.sqlite.org/lang_conflict.html
  - To get uniqueness for root tags is tricky, as NULL is always unique!
    + Need additional check
