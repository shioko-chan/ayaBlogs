use master
if exists (select 1
from sys.databases
where name='ayablogs')
begin
	alter database ayablogs set single_user with rollback immediate
	-- 转换为单用户模式，回滚现有链接，确保删除过程中没有其他用户操作数据库
	drop database ayablogs
end
create database ayablogs
go

use ayablogs
begin transaction
create table avatar
(
	id bigint primary key identity(0,1),
	uuid varchar(36),
	extern_name varchar(10),
	create_at datetime default getdate(),
)

insert into avatar
	(uuid, extern_name)
values('default', 'jpg')

create table usr
(
	id bigint primary key identity(0, 1),
	password_hash varbinary(64) not null,
	salt varbinary(64) not null,
	username nvarchar(20) not null unique,
	email nvarchar(50) not null unique,
	avatar bigint foreign key references avatar(id) null,
	birthday date check(birthday >= '1900-01-01'),
	sex smallint check(sex between 0 and 4),
	intro nvarchar(max),
	is_administrator bit default 0 not null,
)

create table passage
(
	id bigint primary key identity(0, 1),
	heat bigint default 0 not null,
	title nvarchar(255) not null,
	content nvarchar(max) not null,
	create_at datetime default getdate(),
	is_draft bit default 1 not null,
	author_id bigint foreign key references usr(id) on delete cascade,
)


create table img
(
	id bigint primary key identity(0,1),
	uuid varchar(36),
	extern_name varchar(10),
	alt nvarchar(200),
	title nvarchar(200),
	create_at datetime default getdate(),
	contain_by bigint foreign key references passage(id) null,
)

create table comment
(
	id bigint primary key identity(0, 1),
	content nvarchar(500) not null,
	create_at datetime default getdate(),
	author_id bigint foreign key references usr(id),
	contain_by bigint foreign key references passage(id) on delete cascade,
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

create procedure insert_draft
	@title nvarchar(max),
	@content nvarchar(max),
	@author_id bigint,
	@pid bigint out
as
begin
	set nocount on;
	insert into draft
		(title, content, author_id)
	values
		(@title, @content, @author_id);
	set @pid = scope_identity();
end
