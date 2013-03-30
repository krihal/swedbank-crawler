drop table if exists swedbank;
create table swedbank (
       id integer primary key autoincrement,
       time timestamp default (strftime('%s', 'now')),
       value float not null,
       name text not null
);