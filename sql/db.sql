use master
if exists (select 1
from sys.databases
where name='ayablogs')
begin
    alter database ayablogs set single_user with rollback immediate
    drop database ayablogs
end;
create database ayablogs
go

use ayablogs
begin transaction

create table img
(
    uuid uniqueidentifier primary key,
    create_at datetime default getdate(),
)

create table usercredential
(
    id bigint primary key identity(0, 1),
    password_hash varbinary(64) not null,
    salt varbinary(64) not null,
    username nvarchar(20) not null unique,
    email nvarchar(100) not null unique,
    is_administrator bit default 0 not null,
)

create table userprofile
(
    id bigint primary key,
    birthday date check(birthday >= '1900-01-01'),
    avatar uniqueidentifier foreign key references img(uuid),
    intro nvarchar(250),
    create_at datetime default getdate(),
    foreign key (id) references usercredential(id) on delete cascade,
)

create table passage
(
    id bigint primary key identity(0, 1),
    vote_up bigint default 0 not null,
    content nvarchar(max) not null,
    create_at datetime default getdate(),
    is_draft bit default 1 not null,
    author_id bigint foreign key references usercredential(id) on delete cascade,
)

create table diary
(
    id bigint primary key identity(0,1),
    content nvarchar(max) not null,
    create_at datetime default getdate(),
    author_id bigint foreign key references usercredential(id) on delete cascade,
)

create table question
(
    id bigint primary key identity(0, 1),
    vote_up bigint default 0 not null,
    content nvarchar(max) not null,
    create_at datetime default getdate(),
    author_id bigint foreign key references usercredential(id) on delete cascade,
)

create table comment
(
    id bigint primary key identity(0, 1),
    content nvarchar(500) not null,
    create_at datetime default getdate(),
    author_id bigint foreign key references usercredential(id),
    contain_by bigint foreign key references passage(id) on delete cascade,
)

create table answer
(
    id bigint primary key identity(0, 1),
    content nvarchar(max) not null,
    create_at datetime default getdate(),
    author_id bigint foreign key references usercredential(id),
    contain_by bigint foreign key references question(id) on delete cascade,
)

create table passage_img
(
    id bigint foreign key references passage(id),
    uuid uniqueidentifier foreign key references img(uuid),
    primary key (id, uuid),
)

create table diary_img
(
    id bigint foreign key references diary(id),
    uuid uniqueidentifier foreign key references img(uuid),
    primary key (id, uuid),
)

create table question_img
(
    id bigint foreign key references question(id),
    uuid uniqueidentifier foreign key references img(uuid),
    primary key (id, uuid),
)

create table comment_img
(
    id bigint foreign key references comment(id),
    uuid uniqueidentifier foreign key references img(uuid),
    primary key (id, uuid),
)

create table answer_img
(
    id bigint foreign key references answer(id),
    uuid uniqueidentifier foreign key references img(uuid),
    primary key (id, uuid),
)

create table img_deleted
(
    uuid uniqueidentifier,
    create_at datetime default getdate(),
)

create table usercredential_deleted
(
    id bigint,
    password_hash varbinary(64),
    salt varbinary(64),
    username nvarchar(20),
    email nvarchar(100),
    is_administrator bit,
)

create table userprofile_deleted
(
    id bigint,
    birthday date,
    avatar uniqueidentifier,
    intro nvarchar(250),
    create_at datetime,
)

create table passage_deleted
(
    id bigint,
    vote_up bigint,
    content nvarchar(max),
    create_at datetime,
    is_draft bit,
    author_id bigint,
)

create table diary_deleted
(
    id bigint,
    content nvarchar(max),
    create_at datetime,
    author_id bigint,
)

create table question_deleted
(
    id bigint,
    vote_up bigint,
    content nvarchar(max),
    create_at datetime,
    author_id bigint,
)

create table comment_deleted
(
    id bigint,
    content nvarchar(500),
    create_at datetime,
    author_id bigint,
    contain_by bigint,
)

create table answer_deleted
(
    id bigint,
    content nvarchar(max),
    create_at datetime,
    author_id bigint,
    contain_by bigint,
)

create table passage_img_deleted
(
    id bigint,
    uuid uniqueidentifier,
)

create table diary_img_deleted
(
    id bigint,
    uuid uniqueidentifier,
)

create table question_img_deleted
(
    id bigint foreign key references question(id),
    uuid uniqueidentifier foreign key references img(uuid),
)

create table comment_img_deleted
(
    id bigint foreign key references comment(id),
    uuid uniqueidentifier foreign key references img(uuid),
)

create table answer_img_deleted
(
    id bigint foreign key references answer(id),
    uuid uniqueidentifier foreign key references img(uuid),
)

if not exists(select *
from sys.sql_logins
where name='shiori')
	create login shiori with password='password'

create user shiori for login shiori
alter role db_owner add member shiori

if @@error!=0
	rollback transaction
else
	commit transaction
go

create trigger create_profile on usercredential after insert
as
begin
    insert into userprofile
        (id)
    select id
    from inserted
end;
go

create procedure create_delete_trigger
    @table_name nvarchar(max)
as
begin
    declare @sql nvarchar(max);
    declare @deleted_table_name nvarchar(max);
    set @deleted_table_name = @table_name + 'deleted';
    set @sql = 'create trigger trigger_after_delete_'
    + @table_name + ' on ' + @table_name + ' after delete
        as
        begin
            insert into '+ @deleted_table_name +
            ' select * from deleted
        end; ';
    exec sp_executesql @sql
end;
go

exec create_delete_trigger 'avatar';
exec create_delete_trigger 'usercredential';
exec create_delete_trigger 'userprofile';
exec create_delete_trigger 'passageimg';
exec create_delete_trigger 'passage';
exec create_delete_trigger 'passageimgmap';
exec create_delete_trigger 'diaryimg';
exec create_delete_trigger 'diary';
exec create_delete_trigger 'diaryimgmap';
exec create_delete_trigger 'comment';
