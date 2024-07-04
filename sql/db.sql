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
create table usr
(
	id bigint primary key identity(0, 1),
	password_hash varbinary(64) not null,
	salt varbinary(64) not null,
	username nvarchar(20) not null unique,
	email nvarchar(50) not null unique,
	avatar nvarchar(100) default 'default.jpg',
	birthday date check(birthday between '1900-01-01' and '2024-6-25'),
	sex smallint check(sex between 0 and 4),
	intro nvarchar(max),
	is_administrator bit default 0 not null,
)
create table passage
(
	id bigint primary key identity(0, 1),
	title nvarchar(255) not null,
	content nvarchar(max) not null,
	create_at datetime default getdate(),
	author_id bigint foreign key references usr(id) on delete cascade,
)
create table announcement
(
	id bigint primary key identity(0, 1),
	title nvarchar(255) not null,
	content nvarchar(max) not null,
	create_at datetime default getdate(),
	author_id bigint foreign key references usr(id) on delete cascade,
)
create table img
(
	id bigint primary key identity(0,1),
	img_name nvarchar(100),
	describe nvarchar(200),
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
create table vote
(
	id bigint primary key identity(0, 1),
	content nvarchar(255) not null,
	create_at datetime default getdate(),
	author_id bigint foreign key references usr(id) on delete cascade,
)
create table option_item
(
	id bigint primary key identity(0, 1),
	content nvarchar (255) not null,
	vote_cnt bigint default 0,
	contain_by bigint foreign key references vote(id) on delete cascade,
)
create table poll
(
	id bigint primary key identity(0, 1),
	create_at datetime default getdate(),
	poller_id bigint foreign key references usr(id),
	option_item_id bigint foreign key references option_item(id) on delete cascade,
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

create trigger update_vote_cnt on poll
after insert 
as
begin

	update option_item set vote_cnt=vote_cnt+temporary.cnt from (
	select option_item_id, count(*) as cnt
		from inserted
		group by option_item_id) as temporary, option_item
	where option_item.id=temporary.option_item_id
end
go

create procedure insert_passage
	@title nvarchar(max),
	@content nvarchar(max),
	@author_id bigint,
	@pid bigint out
as
begin
	set nocount on;
	insert into passage
		(title, content, author_id)
	values
		(@title, @content, @author_id);
	set @pid = scope_identity();
end
