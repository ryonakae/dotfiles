# 言語別ベストプラクティスリファレンス

このドキュメントは、主要なプログラミング言語のベストプラクティスを解説します。

## 目次

1. [JavaScript / TypeScript](#javascript--typescript)
2. [Python](#python)
3. [Java](#java)
4. [Swift](#swift)
5. [Go](#go)
6. [Rust](#rust)

---

## JavaScript / TypeScript

### 1. `const` / `let` の使い分け

**原則：** 再代入しない変数には `const` を使用。`var` は使用しない。

**悪い例：**
```javascript
var name = "Alice";  // var は使わない
let age = 30;        // 再代入しないなら const を使う
```

**良い例：**
```javascript
const name = "Alice";  // 再代入しない
let age = 30;          // 後で再代入する可能性がある

age = 31;  // OK
```

---

### 2. `async`/`await` の適切な使用

**原則：** Promise を使うより `async`/`await` を優先。エラーハンドリングを忘れない。

**悪い例：**
```javascript
function fetchData() {
  fetch('/api/data')
    .then(response => response.json())
    .then(data => {
      console.log(data);
    });
  // エラーハンドリングがない
}
```

**良い例：**
```javascript
async function fetchData() {
  try {
    const response = await fetch('/api/data');
    const data = await response.json();
    console.log(data);
  } catch (error) {
    console.error('Failed to fetch data:', error);
  }
}
```

**複数の非同期処理を並行実行：**
```javascript
async function fetchMultipleData() {
  try {
    const [users, posts, comments] = await Promise.all([
      fetch('/api/users').then(r => r.json()),
      fetch('/api/posts').then(r => r.json()),
      fetch('/api/comments').then(r => r.json())
    ]);

    return { users, posts, comments };
  } catch (error) {
    console.error('Failed to fetch data:', error);
  }
}
```

---

### 3. 型安全性（TypeScript）

**原則：** `any` の使用を避け、適切な型を定義する。

**悪い例：**
```typescript
function processData(data: any) {  // any は避ける
  return data.map((item: any) => item.value);
}
```

**良い例：**
```typescript
interface DataItem {
  id: number;
  value: string;
}

function processData(data: DataItem[]): string[] {
  return data.map(item => item.value);
}
```

**Union 型の活用：**
```typescript
type Result<T> =
  | { success: true; data: T }
  | { success: false; error: string };

function fetchUser(id: number): Result<User> {
  try {
    const user = getUserById(id);
    return { success: true, data: user };
  } catch (error) {
    return { success: false, error: error.message };
  }
}
```

---

### 4. 不変性（Immutability）

**原則：** 配列やオブジェクトを直接変更せず、新しいコピーを作成する。

**悪い例：**
```javascript
const numbers = [1, 2, 3];
numbers.push(4);  // 元の配列を変更

const user = { name: "Alice", age: 30 };
user.age = 31;  // 元のオブジェクトを変更
```

**良い例：**
```javascript
const numbers = [1, 2, 3];
const newNumbers = [...numbers, 4];  // 新しい配列を作成

const user = { name: "Alice", age: 30 };
const updatedUser = { ...user, age: 31 };  // 新しいオブジェクトを作成
```

**配列メソッドの活用：**
```javascript
// filter, map, reduce などは新しい配列を返す
const numbers = [1, 2, 3, 4, 5];
const evenNumbers = numbers.filter(n => n % 2 === 0);
const doubled = numbers.map(n => n * 2);
const sum = numbers.reduce((acc, n) => acc + n, 0);
```

---

### 5. アロー関数と通常関数の使い分け

**原則：** `this` のバインドが必要な場合以外はアロー関数を使用。

**アロー関数を使うべき場合：**
```javascript
// コールバック
const numbers = [1, 2, 3];
const doubled = numbers.map(n => n * 2);

// 短い関数
const add = (a, b) => a + b;
```

**通常関数を使うべき場合：**
```javascript
// メソッド定義（this を使う場合）
const calculator = {
  value: 0,
  add(n) {  // アロー関数だと this.value にアクセスできない
    this.value += n;
    return this;
  }
};
```

---

### 6. Optional Chaining と Nullish Coalescing

**原則：** ネストしたプロパティへの安全なアクセスには Optional Chaining (`?.`) を使用。

**悪い例：**
```javascript
const userName = user && user.profile && user.profile.name;
const age = user.profile.age !== undefined ? user.profile.age : 0;
```

**良い例：**
```javascript
const userName = user?.profile?.name;
const age = user?.profile?.age ?? 0;  // null/undefined の場合のみ 0
```

---

## Python

### 1. PEP 8 スタイルガイドの遵守

**命名規則：**
```python
# 変数・関数：snake_case
user_name = "Alice"
def calculate_total(): pass

# クラス：PascalCase
class UserProfile: pass

# 定数：UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3

# プライベート：先頭にアンダースコア
def _internal_helper(): pass
```

**インデント：**
```python
# 4 スペース（タブではない）
def my_function():
    if condition:
        do_something()
```

---

### 2. リスト内包表記の活用

**悪い例：**
```python
# 伝統的な for ループ
squared = []
for x in range(10):
    squared.append(x ** 2)
```

**良い例：**
```python
# リスト内包表記
squared = [x ** 2 for x in range(10)]

# 条件付き
even_squared = [x ** 2 for x in range(10) if x % 2 == 0]

# 辞書内包表記
word_lengths = {word: len(word) for word in ["hello", "world"]}

# セット内包表記
unique_lengths = {len(word) for word in ["hello", "world", "hi"]}
```

---

### 3. コンテキストマネージャ（`with` 文）

**原則：** ファイルやデータベース接続など、リソース管理には `with` 文を使用。

**悪い例：**
```python
# ファイルを閉じ忘れる可能性
file = open('data.txt', 'r')
data = file.read()
file.close()  # エラーが発生すると実行されない
```

**良い例：**
```python
# 自動的にファイルが閉じられる
with open('data.txt', 'r') as file:
    data = file.read()

# 複数のリソース
with open('input.txt', 'r') as infile, open('output.txt', 'w') as outfile:
    outfile.write(infile.read())
```

**カスタムコンテキストマネージャ：**
```python
from contextlib import contextmanager

@contextmanager
def database_connection():
    conn = connect_to_database()
    try:
        yield conn
    finally:
        conn.close()

with database_connection() as conn:
    conn.execute("SELECT * FROM users")
```

---

### 4. 型ヒント（Type Hints）

**原則：** Python 3.5+ では型ヒントを活用して可読性と保守性を向上。

**基本的な型ヒント：**
```python
def greet(name: str) -> str:
    return f"Hello, {name}"

def add(a: int, b: int) -> int:
    return a + b

# リスト、辞書
from typing import List, Dict

def process_items(items: List[str]) -> Dict[str, int]:
    return {item: len(item) for item in items}
```

**Optional と Union：**
```python
from typing import Optional, Union

def find_user(user_id: int) -> Optional[User]:
    # User または None を返す
    pass

def process_value(value: Union[int, str]) -> str:
    # int または str を受け取る
    return str(value)
```

**ジェネリクス：**
```python
from typing import TypeVar, Generic, List

T = TypeVar('T')

class Stack(Generic[T]):
    def __init__(self) -> None:
        self.items: List[T] = []

    def push(self, item: T) -> None:
        self.items.append(item)

    def pop(self) -> T:
        return self.items.pop()
```

---

### 5. 例外処理の適切性

**原則：** bare except を避け、具体的な例外をキャッチする。

**悪い例：**
```python
try:
    result = risky_operation()
except:  # すべての例外をキャッチ（KeyboardInterrupt も）
    print("Error occurred")
```

**良い例：**
```python
try:
    result = risky_operation()
except ValueError as e:
    print(f"Invalid value: {e}")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
    raise  # 再送出
```

**カスタム例外：**
```python
class ValidationError(Exception):
    """入力値の検証エラー"""
    pass

def validate_age(age: int) -> None:
    if age < 0:
        raise ValidationError("Age cannot be negative")
    if age > 150:
        raise ValidationError("Age is unrealistic")
```

---

### 6. f-strings の使用

**原則：** 文字列フォーマットには f-strings（Python 3.6+）を優先。

**悪い例：**
```python
name = "Alice"
age = 30
message = "My name is %s and I am %d years old" % (name, age)
message = "My name is {} and I am {} years old".format(name, age)
```

**良い例：**
```python
name = "Alice"
age = 30
message = f"My name is {name} and I am {age} years old"

# 式の評価
price = 19.99
message = f"Total: ${price * 1.1:.2f}"  # Total: $21.99
```

---

## Java

### 1. `Optional` の使用

**原則：** `null` チェックの代わりに `Optional` を使用。

**悪い例：**
```java
public User findUser(int id) {
    // null を返す可能性
    return null;
}

User user = findUser(123);
if (user != null) {
    System.out.println(user.getName());
}
```

**良い例：**
```java
public Optional<User> findUser(int id) {
    // Optional でラップして返す
    User user = database.query(id);
    return Optional.ofNullable(user);
}

Optional<User> userOpt = findUser(123);
userOpt.ifPresent(user -> System.out.println(user.getName()));

// または
String userName = findUser(123)
    .map(User::getName)
    .orElse("Unknown");
```

---

### 2. Stream API の活用

**原則：** コレクション操作には Stream API を使用。

**悪い例：**
```java
List<String> names = new ArrayList<>();
for (User user : users) {
    if (user.getAge() >= 18) {
        names.add(user.getName());
    }
}
```

**良い例：**
```java
List<String> names = users.stream()
    .filter(user -> user.getAge() >= 18)
    .map(User::getName)
    .collect(Collectors.toList());

// 統計処理
int totalAge = users.stream()
    .mapToInt(User::getAge)
    .sum();

double averageAge = users.stream()
    .mapToInt(User::getAge)
    .average()
    .orElse(0.0);
```

---

### 3. `try-with-resources` の使用

**原則：** リソース管理には `try-with-resources` を使用。

**悪い例：**
```java
BufferedReader reader = null;
try {
    reader = new BufferedReader(new FileReader("file.txt"));
    String line = reader.readLine();
} catch (IOException e) {
    e.printStackTrace();
} finally {
    if (reader != null) {
        try {
            reader.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
```

**良い例：**
```java
try (BufferedReader reader = new BufferedReader(new FileReader("file.txt"))) {
    String line = reader.readLine();
} catch (IOException e) {
    e.printStackTrace();
}

// 複数のリソース
try (
    FileInputStream input = new FileInputStream("input.txt");
    FileOutputStream output = new FileOutputStream("output.txt")
) {
    // 処理
}
```

---

### 4. 適切な例外処理

**原則：** チェック例外と非チェック例外を適切に使い分ける。

**チェック例外（回復可能なエラー）：**
```java
public void readFile(String path) throws IOException {
    // 呼び出し側で処理を強制
}
```

**非チェック例外（プログラミングエラー）：**
```java
public void validateAge(int age) {
    if (age < 0) {
        throw new IllegalArgumentException("Age cannot be negative");
    }
}
```

---

### 5. ラムダ式とメソッド参照

**原則：** 簡潔に書けるラムダ式やメソッド参照を活用。

**悪い例：**
```java
users.sort(new Comparator<User>() {
    @Override
    public int compare(User u1, User u2) {
        return u1.getName().compareTo(u2.getName());
    }
});
```

**良い例：**
```java
// ラムダ式
users.sort((u1, u2) -> u1.getName().compareTo(u2.getName()));

// メソッド参照
users.sort(Comparator.comparing(User::getName));
```

---

## Swift

### 1. Optional の安全な扱い

**原則：** forced unwrap (`!`) を避け、安全な方法で unwrap する。

**悪い例：**
```swift
let name: String? = getName()
print(name!)  // クラッシュの可能性
```

**良い例：**
```swift
// Optional Binding
if let name = getName() {
    print(name)
}

// Optional Chaining
let length = user?.name?.count

// Nil Coalescing
let userName = getName() ?? "Unknown"

// Guard 文
guard let name = getName() else {
    return
}
print(name)
```

---

### 2. プロトコル指向プログラミング

**原則：** 継承よりもプロトコルを優先。

**悪い例：**
```swift
class Animal {
    func makeSound() {
        fatalError("Subclass must implement")
    }
}

class Dog: Animal {
    override func makeSound() {
        print("Woof!")
    }
}
```

**良い例：**
```swift
protocol Animal {
    func makeSound()
}

struct Dog: Animal {
    func makeSound() {
        print("Woof!")
    }
}

struct Cat: Animal {
    func makeSound() {
        print("Meow!")
    }
}
```

**プロトコルエクステンション：**
```swift
protocol Drawable {
    func draw()
}

extension Drawable {
    func draw() {
        print("Default drawing")
    }

    func describe() {
        print("This is a drawable object")
    }
}
```

---

### 3. メモリ管理

**原則：** strong、weak、unowned を適切に使い分けて循環参照を避ける。

**悪い例：**
```swift
class Person {
    var apartment: Apartment?
}

class Apartment {
    var tenant: Person?  // 循環参照
}
```

**良い例：**
```swift
class Person {
    var apartment: Apartment?
}

class Apartment {
    weak var tenant: Person?  // weak で循環参照を回避
}
```

**クロージャでの循環参照回避：**
```swift
class ViewController {
    var name = "ViewController"

    func setupClosure() {
        // 悪い例
        someAsyncOperation {
            print(self.name)  // self を強参照
        }

        // 良い例
        someAsyncOperation { [weak self] in
            guard let self = self else { return }
            print(self.name)
        }
    }
}
```

---

### 4. `guard` 文の活用

**原則：** 早期リターンには `guard` 文を使用。

**悪い例：**
```swift
func processUser(user: User?) {
    if let user = user {
        if user.isActive {
            if user.hasPermission {
                // 深いネスト
                performAction(user)
            }
        }
    }
}
```

**良い例：**
```swift
func processUser(user: User?) {
    guard let user = user else {
        return
    }

    guard user.isActive else {
        return
    }

    guard user.hasPermission else {
        return
    }

    // フラットなコード
    performAction(user)
}
```

---

### 5. Value Type の優先

**原則：** 可能な限り `struct` や `enum` を使用（参照型より値型を優先）。

**struct を使うべき場合：**
```swift
struct Point {
    var x: Double
    var y: Double
}

struct User {
    var name: String
    var age: Int
}
```

**class を使うべき場合：**
```swift
// 継承が必要
class Vehicle {
    func start() {}
}

// 参照セマンティクスが必要
class DatabaseConnection {
    // 複数の場所から同じインスタンスを共有
}
```

---

## Go

### 1. エラーハンドリングの徹底

**原則：** エラーを無視せず、適切に処理する。

**悪い例：**
```go
file, _ := os.Open("file.txt")  // エラーを無視
defer file.Close()
```

**良い例：**
```go
file, err := os.Open("file.txt")
if err != nil {
    return fmt.Errorf("failed to open file: %w", err)
}
defer file.Close()
```

**エラーのラップ：**
```go
func readConfig(path string) (*Config, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return nil, fmt.Errorf("read config file: %w", err)
    }

    var config Config
    if err := json.Unmarshal(data, &config); err != nil {
        return nil, fmt.Errorf("parse config: %w", err)
    }

    return &config, nil
}
```

---

### 2. `defer` の適切な使用

**原則：** リソースのクリーンアップには `defer` を使用。

**良い例：**
```go
func processFile(path string) error {
    file, err := os.Open(path)
    if err != nil {
        return err
    }
    defer file.Close()  // 関数終了時に必ず実行

    // ファイル処理
    return nil
}

// 複数の defer（LIFO 順で実行）
func example() {
    defer fmt.Println("3")
    defer fmt.Println("2")
    defer fmt.Println("1")
}  // 出力: 1, 2, 3
```

**Mutex のロック解除：**
```go
func (c *Counter) Increment() {
    c.mu.Lock()
    defer c.mu.Unlock()

    c.value++
}
```

---

### 3. インターフェースの小さく保つ設計

**原則：** インターフェースは小さく、焦点を絞った設計にする。

**悪い例：**
```go
type Database interface {
    Connect() error
    Disconnect() error
    Query(sql string) ([]Row, error)
    Insert(table string, data interface{}) error
    Update(table string, data interface{}) error
    Delete(table string, id int) error
    BeginTransaction() error
    Commit() error
    Rollback() error
}
```

**良い例：**
```go
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

type ReadWriter interface {
    Reader
    Writer
}
```

---

### 4. goroutine の適切な管理

**原則：** goroutine のライフサイクルを適切に管理する。

**悪い例：**
```go
for _, url := range urls {
    go fetchURL(url)  // goroutine の完了を待たない
}
// プログラムが終了し、goroutine が途中で終わる
```

**良い例：**
```go
var wg sync.WaitGroup

for _, url := range urls {
    wg.Add(1)
    go func(url string) {
        defer wg.Done()
        fetchURL(url)
    }(url)
}

wg.Wait()  // すべての goroutine が完了するまで待つ
```

**Context を使った goroutine のキャンセル：**
```go
func worker(ctx context.Context) {
    for {
        select {
        case <-ctx.Done():
            return  // キャンセルされた
        default:
            // 処理
        }
    }
}

ctx, cancel := context.WithCancel(context.Background())
go worker(ctx)

// 後でキャンセル
cancel()
```

---

### 5. ゼロ値の活用

**原則：** ゼロ値で有用な状態にする設計。

**良い例：**
```go
type Buffer struct {
    data []byte
}

// ゼロ値でそのまま使える
var buf Buffer
buf.Write([]byte("hello"))

// sync.Mutex もゼロ値で使える
var mu sync.Mutex
mu.Lock()
```

---

## Rust

### 1. 所有権と借用の適切な使用

**原則：** 所有権システムを理解し、適切に借用する。

**所有権の移動：**
```rust
fn main() {
    let s1 = String::from("hello");
    let s2 = s1;  // s1 の所有権が s2 に移動
    // println!("{}", s1);  // エラー：s1 はもう使えない
    println!("{}", s2);  // OK
}
```

**借用（参照）：**
```rust
fn main() {
    let s1 = String::from("hello");
    let len = calculate_length(&s1);  // 借用
    println!("The length of '{}' is {}", s1, len);  // s1 はまだ使える
}

fn calculate_length(s: &String) -> usize {
    s.len()
}
```

**可変借用：**
```rust
fn main() {
    let mut s = String::from("hello");
    change(&mut s);
    println!("{}", s);  // "hello, world"
}

fn change(s: &mut String) {
    s.push_str(", world");
}
```

---

### 2. `Result` 型によるエラーハンドリング

**原則：** エラー処理には `Result` 型を使用。`unwrap()` は本番コードでは避ける。

**悪い例：**
```rust
let file = File::open("file.txt").unwrap();  // パニックの可能性
```

**良い例：**
```rust
use std::fs::File;
use std::io::Read;

fn read_file(path: &str) -> Result<String, std::io::Error> {
    let mut file = File::open(path)?;  // ? 演算子でエラーを伝播
    let mut contents = String::new();
    file.read_to_string(&mut contents)?;
    Ok(contents)
}

fn main() {
    match read_file("file.txt") {
        Ok(contents) => println!("{}", contents),
        Err(e) => eprintln!("Error: {}", e),
    }
}
```

---

### 3. パターンマッチングの活用

**原則：** `match` や `if let` で明示的にパターンマッチング。

**基本的な match：**
```rust
enum Message {
    Quit,
    Move { x: i32, y: i32 },
    Write(String),
}

fn process_message(msg: Message) {
    match msg {
        Message::Quit => println!("Quit"),
        Message::Move { x, y } => println!("Move to ({}, {})", x, y),
        Message::Write(text) => println!("Write: {}", text),
    }
}
```

**`if let` で簡潔に：**
```rust
let some_value = Some(3);

if let Some(x) = some_value {
    println!("Value: {}", x);
}
```

---

### 4. `unwrap()` の使用を避ける

**原則：** 本番コードでは `unwrap()` や `expect()` を避け、適切にエラーを処理する。

**悪い例：**
```rust
let result = parse_number("abc").unwrap();  // パニック
```

**良い例：**
```rust
match parse_number("abc") {
    Ok(n) => println!("Number: {}", n),
    Err(e) => eprintln!("Failed to parse: {}", e),
}

// または ? 演算子
let result = parse_number("abc")?;
```

**テストコードでは OK：**
```rust
#[test]
fn test_parse_number() {
    let result = parse_number("123").unwrap();  // テストでは OK
    assert_eq!(result, 123);
}
```

---

### 5. イテレータの活用

**原則：** ループよりもイテレータメソッドを優先。

**悪い例：**
```rust
let mut sum = 0;
for i in 0..10 {
    if i % 2 == 0 {
        sum += i * 2;
    }
}
```

**良い例：**
```rust
let sum: i32 = (0..10)
    .filter(|x| x % 2 == 0)
    .map(|x| x * 2)
    .sum();
```

**イテレータの連鎖：**
```rust
let names: Vec<String> = users
    .iter()
    .filter(|user| user.age >= 18)
    .map(|user| user.name.clone())
    .collect();
```

---

## まとめ

各言語には独自の慣用的な書き方（idioms）があります。これらのベストプラクティスを適用することで：

- **可読性の向上**：コードが理解しやすくなる
- **保守性の向上**：変更や拡張が容易になる
- **バグの削減**：言語の機能を正しく使うことでバグを防ぐ
- **パフォーマンス**：最適化された言語機能を活用

ただし、すべてのルールには例外があります。コンテキストに応じて適切に判断してください。
