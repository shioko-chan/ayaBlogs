if exists (select * from sys.databases where name='ayablogs')
begin
	alter database ayablogs set single_user with rollback immediate -- 转换为单用户模式，回滚现有链接，确保删除过程中没有其他用户操作数据库
	drop database ayablogs
end
create database ayablogs
use ayablogs
begin transaction
create table usr(
	uid bigint primary key identity(0, 1),
	passwordhash varbinary(64) not null,
	salt varbinary(32) not null,
	uname nvarchar(20) not null,
	ubirthday date,
	usex smallint,
	uintro nvarchar(max)
)
create table passage(
	pid bigint primary key identity(0, 1),
	content nvarchar(max) not null,
	title nvarchar(255) not null,
	createAt datetime default getdate(),
	author bigint foreign key references usr(uid) on delete cascade
)
create table images(
	imgid bigint primary key identity(0,1),
	imgpath varchar(100),
	containBy bigint foreign key references passage(pid) null
)
alter table usr add avatar bigint foreign key references images(imgid)
create table comment(
	cid bigint primary key identity(0, 1),
	commenter bigint foreign key references usr(uid) on delete cascade,
	passage bigint foreign key references passage(pid) on delete cascade,
	content nvarchar(500) not null,
	createAt datetime default getdate()
)
create table vote(
	vid bigint primary key identity(0, 1),
	creator bigint foreign key references usr(uid) on delete cascade,
	title nvarchar(255) not null,
	content nvarchar(max) not null,
	choices varchar(max) not null,
	choicesCnt smallint not null,
	createAt datetime default getdate()
)
create table poll(
	poid bigint primary key identity(0, 1),
	poller bigint foreign key references usr(uid) on delete cascade,
	voted bigint foreign key references vote(vid) on delete cascade,
	attitude smallint not null,
	createAt datetime default getdate(),
)
if @@error!=0
	rollback transaction
else
	commit transaction
go
create trigger deleteImages on passage
after delete
as
begin
	delete from images
	where images.containBy in (select pid from deleted)
end