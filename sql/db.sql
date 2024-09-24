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
    rc bigint default 0 not null,
    create_at datetime default getdate() not null,
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
    avatar uniqueidentifier foreign key references img(uuid) on delete cascade,
    intro nvarchar(250),
    create_at datetime default getdate(),
    is_passage_visible bit default 1 not null,
    is_question_visible bit default 1 not null,
    is_comment_visible bit default 1 not null,
    is_answer_visible bit default 1 not null,
    foreign key (id) references usercredential(id) on delete cascade,
)

create table passage
(
    id bigint primary key identity(0, 1),
    content nvarchar(max) not null,
    create_at datetime default getdate(),
    author_id bigint foreign key references usercredential(id) on delete cascade,
    vote_up bigint default 0 not null,
    is_draft bit default 1 not null,
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
    content nvarchar(max) not null,
    create_at datetime default getdate(),
    author_id bigint foreign key references usercredential(id) on delete cascade,
    vote_up bigint default 0 not null,
    title nvarchar(250) not null,
)

create table comment
(
    id bigint primary key identity(0, 1),
    content nvarchar(500) not null,
    create_at datetime default getdate(),
    author_id bigint foreign key references usercredential(id) on delete cascade,
    contain_by bigint foreign key references passage(id),
)

create table answer
(
    id bigint primary key identity(0, 1),
    content nvarchar(max) not null,
    create_at datetime default getdate(),
    author_id bigint foreign key references usercredential(id) on delete cascade,
    contain_by bigint foreign key references question(id),
    vote_up bigint default 0 not null,
)

create table vote_up_passage
(
    id bigint foreign key references usercredential(id) on delete cascade,
    passage_id bigint foreign key references passage(id) on delete cascade,
    create_at datetime default getdate(),
    primary key (id, passage_id),
)

create table vote_up_answer
(
    id bigint foreign key references usercredential(id) on delete cascade,
    answer_id bigint foreign key references answer(id) on delete cascade,
    create_at datetime default getdate(),
    primary key (id, answer_id),
)

create table vote_up_question
(
    id bigint foreign key references usercredential(id) on delete cascade,
    question_id bigint foreign key references question(id) on delete cascade,
    create_at datetime default getdate(),
    primary key (id, question_id),
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

create procedure CreateVoteTrigger
    @TableName nvarchar(64)
as
begin
    declare @sql nvarchar(max);
    set @sql='create trigger sub_vote_up_' + @TableName + ' on vote_up_' + @TableName + ' after delete
    as
    begin
        set nocount on;
        update ' + @TableName + '
        set vote_up=
        case
            when vote_up-d.vote_count<0 then 0
            else vote_up-d.vote_count
        end
        from ' + @TableName + ' p
        inner join(
            select ' + @TableName + '_id as id, count(*) as vote_count
            from deleted
            group by ' + @TableName + '_id
        ) as d on p.id=d.id;
    end;';
    exec sp_executesql @sql;
    set @sql='create trigger add_vote_up_' + @TableName + ' on vote_up_' + @TableName + ' after insert
    as
    begin
        set nocount on;
        update ' + @TableName + '
        set vote_up=vote_up+d.vote_count
        from ' + @TableName + ' p
        inner join(
            select ' + @TableName + '_id as id, count(*) as vote_count
            from inserted
            group by ' + @TableName + '_id
        ) as d on p.id=d.id
    end;'
    exec sp_executesql @sql;
end
go

exec CreateVoteTrigger 'passage';
exec CreateVoteTrigger 'answer';
exec CreateVoteTrigger 'question';
go
