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

create table avatar
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
    email nvarchar(50) not null unique,
    is_administrator bit default 0 not null,
)

create table userprofile
(
    id bigint primary key,
    birthday date check(birthday >= '1900-01-01'),
    avatar uniqueidentifier foreign key references avatar(uuid),
    intro nvarchar(2000),
    create_at datetime default getdate(),
    foreign key (id) references usercredential(id) on delete cascade,
)


create table passage_img
(
    uuid uniqueidentifier primary key,
    create_at datetime default getdate(),
)

create table passage
(
    id bigint primary key identity(0, 1),
    heat bigint default 0 not null,
    content nvarchar(max) not null,
    create_at datetime default getdate(),
    is_draft bit default 1 not null,
    author_id bigint foreign key references usercredential(id) on delete cascade,
)

create table passage_img_map
(
    id bigint foreign key references passage(id),
    uuid uniqueidentifier foreign key references passage_img(uuid),
    primary key (id, uuid)
)

create table diary_img
(
    uuid uniqueidentifier primary key,
    create_at datetime default getdate(),
)

create table diary
(
    id bigint primary key identity(0,1),
    content nvarchar(max) not null,
    create_at datetime default getdate(),
    author_id bigint foreign key references usercredential(id) on delete cascade,
)

create table diary_img_map
(
    id bigint foreign key references diary(id),
    uuid uniqueidentifier foreign key references diary_img(uuid),
    primary key (id, uuid)
)

create table comment
(
    id bigint primary key identity(0, 1),
    content nvarchar(500) not null,
    create_at datetime default getdate(),
    author_id bigint foreign key references usercredential(id),
    contain_by bigint foreign key references passage(id) on delete cascade,
)


create table avatar_deleted
(
    uuid uniqueidentifier primary key,
    create_at datetime,
)

create table usercredential_deleted
(
    id bigint primary key,
    password_hash varbinary(64),
    salt varbinary(64),
    username nvarchar(20),
    email nvarchar(50),
    is_administrator bit,
)

create table userprofile_deleted
(
    id bigint primary key,
    birthday date,
    avatar uniqueidentifier,
    intro nvarchar(2000),
    create_at datetime,
)

create table passage_img_deleted
(
    uuid uniqueidentifier primary key,
    create_at datetime,
)

create table passage_deleted
(
    id bigint primary key,
    heat bigint,
    content nvarchar(max),
    create_at datetime,
    is_draft bit,
    author_id bigint,
)

create table passage_img_map_deleted
(
    id bigint,
    uuid uniqueidentifier,
    primary key (id, uuid)
)

create table diary_img_deleted
(
    uuid uniqueidentifier primary key,
    create_at datetime,
)

create table diary_deleted
(
    id bigint primary key,
    content nvarchar(max),
    create_at datetime,
    author_id bigint,
)

create table diary_img_map_deleted
(
    id bigint,
    uuid uniqueidentifier,
    primary key (id, uuid)
)

create table comment_deleted
(
    id bigint primary key,
    content nvarchar(500),
    create_at datetime,
    author_id bigint,
    contain_by bigint,
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
    set @deleted_table_name = @table_name + '_deleted';
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
exec create_delete_trigger 'passage_img';
exec create_delete_trigger 'passage';
exec create_delete_trigger 'passage_img_map';
exec create_delete_trigger 'diary_img';
exec create_delete_trigger 'diary';
exec create_delete_trigger 'diary_img_map';
exec create_delete_trigger 'comment';
