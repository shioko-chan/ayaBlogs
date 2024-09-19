-- 向 passage 表中插入支持 Markdown 语法的文章
delete from passage
-- 文章 1
INSERT INTO passage
    (content, is_draft, author_id)
VALUES
    (
        '# 标题 1
这是一篇测试文章，内容支持 Markdown 语法。
## 子标题
- 列表项 1
- 列表项 2
**加粗文本**
*斜体文本*
[链接](http://example.com)
`代码片段`
```python
# Python 代码块
def hello_world():
    print("Hello, world!")
```
> 引用文本
',
        0, 0
);

-- 文章 2
INSERT INTO passage
    (content, is_draft, author_id)
VALUES
    (
        '
# 标题 2
这是另一篇测试文章，内容也支持 Markdown 语法。
## 子标题
1. 有序列表项 1
2. 有序列表项 2
**加粗文本**
*斜体文本*
[链接](http://example.com)
`代码片段`
```html
<!-- HTML 代码块 -->
<div>
    <p>Hello, world!</p>
</div>
```
> 引用文本
',
        0, 0
);

-- 文章 3
INSERT INTO passage
    (content, is_draft, author_id)
VALUES
    (
        '
# 标题 3
这是一篇 Markdown 支持的测试文章。
## 子标题
- 项目 1
- 项目 2
**加粗文本**
*斜体文本*
[链接](http://example.com)
`代码片段`
```javascript
// JavaScript 代码块
function greet() {
    console.log("Hello, world!");
}
```
>> 引用文本
',
        0, 0
);
select *
from passage_deleted
select *
from passage

delete from usr where id=1

insert into passage
    (author_id, content, is_draft)
values(0, '```
int main(){
	std::cout<<"Hello World"<<std::endl;
}
```
```
trait HelloWorld{
	fn sayhello(){
			println!("Hello World");
	}
}
struct foo;
impl HelloWorld for foo;
fn main(){
	foo().sayhello();
}
```
', 0)

insert into passage
    (author_id, content, is_draft)
VALUES(0,
        '
## JavaScript 异步编程：概念与实践

在 JavaScript 中，异步编程是一种处理耗时任务的方式，如网络请求、文件操作和计时器等。本文将介绍 JavaScript 中的几种常见异步编程方式，包括 **回调函数**、**Promise** 和 **Async/Await**。

### 1. 回调函数 (Callback)

回调函数是最基本的异步编程方式。通过将函数作为参数传递给另一个函数，当异步任务完成时调用该回调函数。

#### 示例：

```javascript
function fetchData(callback) {
  setTimeout(() => {
    callback("数据加载完成");
  }, 2000);
}

fetchData((data) => {
  console.log(data); // 输出: "数据加载完成"
});
```

虽然回调函数简单易用，但在处理多个异步操作时容易产生“回调地狱”（Callback Hell），代码难以阅读和维护。

### 2. Promise

`Promise` 是 ES6 引入的一种解决回调地狱的方案，它可以更清晰地表达异步任务的状态（*pending*、*resolved*、*rejected*）。一个 `Promise` 实例代表一个异步操作的最终完成或失败及其结果值。

#### 示例：

```javascript
function fetchData() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve("数据加载完成");
    }, 2000);
  });
}

fetchData()
  .then((data) => {
    console.log(data); // 输出: "数据加载完成"
  })
  .catch((error) => {
    console.error(error);
  });
```

通过 `.then()` 和 `.catch()` 链式调用，`Promise` 提供了一种更加优雅的方式来处理异步操作。

### 3. Async/Await

`Async/Await` 是基于 `Promise` 的语法糖，使异步代码看起来更像同步代码，从而提高了代码的可读性。使用 `async` 声明一个函数为异步函数，使用 `await` 等待一个 `Promise` 完成。

#### 示例：

```javascript
async function fetchData() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve("数据加载完成");
    }, 2000);
  });
}

async function getData() {
  try {
    const data = await fetchData();
    console.log(data); // 输出: "数据加载完成"
  } catch (error) {
    console.error(error);
  }
}

getData();
```

`Async/Await` 使得异步代码的书写和理解变得更加直观，更符合人类的思维方式。

### 4. 异步编程的选择

选择合适的异步编程方式取决于具体场景：

- **回调函数**：简单的异步任务，但会带来回调地狱问题。
- **Promise**：适合复杂的异步任务，支持链式调用，避免了回调地狱。
- **Async/Await**：语法简单直观，推荐用于处理复杂的异步逻辑。

### 5. 总结

JavaScript 异步编程是前端开发中的重要知识点。通过理解和掌握回调函数、Promise 和 Async/Await，你可以编写更高效、更易维护的异步代码。随着异步编程的不断发展，选择合适的工具和方法来解决实际问题尤为重要。

'
, 0)
