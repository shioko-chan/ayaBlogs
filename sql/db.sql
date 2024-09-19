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


create table passageimg
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

create table passageimgmap
(
    id bigint foreign key references passage(id),
    uuid uniqueidentifier foreign key references passageimg(uuid),
    primary key (id, uuid)
)

create table diaryimg
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

create table diaryimgmap
(
    id bigint foreign key references diary(id),
    uuid uniqueidentifier foreign key references diaryimg(uuid),
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


create table avatardeleted
(
    uuid uniqueidentifier primary key,
    create_at datetime,
)

create table usercredentialdeleted
(
    id bigint primary key,
    password_hash varbinary(64),
    salt varbinary(64),
    username nvarchar(20),
    email nvarchar(50),
    is_administrator bit,
)

create table userprofiledeleted
(
    id bigint primary key,
    birthday date,
    avatar uniqueidentifier,
    intro nvarchar(2000),
    create_at datetime,
)

create table passageimgdeleted
(
    uuid uniqueidentifier primary key,
    create_at datetime,
)

create table passagedeleted
(
    id bigint primary key,
    heat bigint,
    content nvarchar(max),
    create_at datetime,
    isDraft bit,
    author_id bigint,
)

create table passageimgmapdeleted
(
    id bigint,
    uuid uniqueidentifier,
    primary key (id, uuid)
)

create table diaryimgdeleted
(
    uuid uniqueidentifier primary key,
    create_at datetime,
)

create table diarydeleted
(
    id bigint primary key,
    content nvarchar(max),
    create_at datetime,
    author_id bigint,
)

create table diaryimgmapdeleted
(
    id bigint,
    uuid uniqueidentifier,
    primary key (id, uuid)
)

create table commentdeleted
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
