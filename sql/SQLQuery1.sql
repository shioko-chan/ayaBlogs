-- �� passage ���в���֧�� Markdown �﷨������
delete from passage
-- ���� 1
INSERT INTO passage
    (content, is_draft, author_id)
VALUES
    (
        '# ���� 1
����һƪ�������£�����֧�� Markdown �﷨��
## �ӱ���
- �б��� 1
- �б��� 2
**�Ӵ��ı�**
*б���ı�*
[����](http://example.com)
`����Ƭ��`
```python
# Python �����
def hello_world():
    print("Hello, world!")
```
> �����ı�
',
        0, 0
);

-- ���� 2
INSERT INTO passage
    (content, is_draft, author_id)
VALUES
    (
        '
# ���� 2
������һƪ�������£�����Ҳ֧�� Markdown �﷨��
## �ӱ���
1. �����б��� 1
2. �����б��� 2
**�Ӵ��ı�**
*б���ı�*
[����](http://example.com)
`����Ƭ��`
```html
<!-- HTML ����� -->
<div>
    <p>Hello, world!</p>
</div>
```
> �����ı�
',
        0, 0
);

-- ���� 3
INSERT INTO passage
    (content, is_draft, author_id)
VALUES
    (
        '
# ���� 3
����һƪ Markdown ֧�ֵĲ������¡�
## �ӱ���
- ��Ŀ 1
- ��Ŀ 2
**�Ӵ��ı�**
*б���ı�*
[����](http://example.com)
`����Ƭ��`
```javascript
// JavaScript �����
function greet() {
    console.log("Hello, world!");
}
```
>> �����ı�
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
## JavaScript �첽��̣�������ʵ��

�� JavaScript �У��첽�����һ�ִ����ʱ����ķ�ʽ�������������ļ������ͼ�ʱ���ȡ����Ľ����� JavaScript �еļ��ֳ����첽��̷�ʽ������ **�ص�����**��**Promise** �� **Async/Await**��

### 1. �ص����� (Callback)

�ص���������������첽��̷�ʽ��ͨ����������Ϊ�������ݸ���һ�����������첽�������ʱ���øûص�������

#### ʾ����

```javascript
function fetchData(callback) {
  setTimeout(() => {
    callback("���ݼ������");
  }, 2000);
}

fetchData((data) => {
  console.log(data); // ���: "���ݼ������"
});
```

��Ȼ�ص����������ã����ڴ������첽����ʱ���ײ������ص���������Callback Hell�������������Ķ���ά����

### 2. Promise

`Promise` �� ES6 �����һ�ֽ���ص������ķ����������Ը������ر���첽�����״̬��*pending*��*resolved*��*rejected*����һ�� `Promise` ʵ������һ���첽������������ɻ�ʧ�ܼ�����ֵ��

#### ʾ����

```javascript
function fetchData() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve("���ݼ������");
    }, 2000);
  });
}

fetchData()
  .then((data) => {
    console.log(data); // ���: "���ݼ������"
  })
  .catch((error) => {
    console.error(error);
  });
```

ͨ�� `.then()` �� `.catch()` ��ʽ���ã�`Promise` �ṩ��һ�ָ������ŵķ�ʽ�������첽������

### 3. Async/Await

`Async/Await` �ǻ��� `Promise` ���﷨�ǣ�ʹ�첽���뿴��������ͬ�����룬�Ӷ�����˴���Ŀɶ��ԡ�ʹ�� `async` ����һ������Ϊ�첽������ʹ�� `await` �ȴ�һ�� `Promise` ��ɡ�

#### ʾ����

```javascript
async function fetchData() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve("���ݼ������");
    }, 2000);
  });
}

async function getData() {
  try {
    const data = await fetchData();
    console.log(data); // ���: "���ݼ������"
  } catch (error) {
    console.error(error);
  }
}

getData();
```

`Async/Await` ʹ���첽�������д������ø���ֱ�ۣ������������˼ά��ʽ��

### 4. �첽��̵�ѡ��

ѡ����ʵ��첽��̷�ʽȡ���ھ��峡����

- **�ص�����**���򵥵��첽���񣬵�������ص��������⡣
- **Promise**���ʺϸ��ӵ��첽����֧����ʽ���ã������˻ص�������
- **Async/Await**���﷨��ֱ�ۣ��Ƽ����ڴ����ӵ��첽�߼���

### 5. �ܽ�

JavaScript �첽�����ǰ�˿����е���Ҫ֪ʶ�㡣ͨ���������ջص�������Promise �� Async/Await������Ա�д����Ч������ά�����첽���롣�����첽��̵Ĳ��Ϸ�չ��ѡ����ʵĹ��ߺͷ��������ʵ��������Ϊ��Ҫ��

'
, 0)
