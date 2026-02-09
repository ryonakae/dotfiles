# プログラミング原則リファレンス

このドキュメントは、コードレビュー時に参照する主要なプログラミング原則を詳細に解説します。

## 目次

1. [SOLID 原則](#solid-原則)
2. [DRY（Don't Repeat Yourself）](#dry-dont-repeat-yourself)
3. [KISS（Keep It Simple, Stupid）](#kiss-keep-it-simple-stupid)
4. [YAGNI（You Aren't Gonna Need It）](#yagni-you-arent-gonna-need-it)
5. [関心の分離（Separation of Concerns）](#関心の分離-separation-of-concerns)
6. [コンポジション vs 継承](#コンポジション-vs-継承)
7. [早期リターン（Early Return）](#早期リターン-early-return)
8. [ガード節（Guard Clauses）](#ガード節-guard-clauses)

---

## SOLID 原則

SOLID は、オブジェクト指向プログラミングにおける5つの設計原則の頭文字を取ったものです。

### 1. Single Responsibility Principle（単一責任の原則）

**定義：** クラスや関数は、ただ1つの責任（変更する理由）だけを持つべき。

**悪い例：**
```typescript
class User {
  constructor(public name: string, public email: string) {}

  // ユーザーデータの永続化（責任1）
  save() {
    database.save(this);
  }

  // メール送信（責任2）
  sendEmail(message: string) {
    emailService.send(this.email, message);
  }

  // ログ出力（責任3）
  log(action: string) {
    console.log(`${this.name} performed ${action}`);
  }
}
```

**良い例：**
```typescript
class User {
  constructor(public name: string, public email: string) {}
}

class UserRepository {
  save(user: User) {
    database.save(user);
  }
}

class EmailService {
  sendToUser(user: User, message: string) {
    this.send(user.email, message);
  }
}

class UserLogger {
  log(user: User, action: string) {
    console.log(`${user.name} performed ${action}`);
  }
}
```

**チェックポイント：**
- クラス/関数に複数の責任が含まれていないか
- 変更する理由が複数ないか
- クラス名/関数名が「and」や「or」を含んでいないか

---

### 2. Open/Closed Principle（オープン・クローズドの原則）

**定義：** ソフトウェアのエンティティ（クラス、モジュール、関数）は、拡張に対して開かれているべきだが、修正に対しては閉じているべき。

**悪い例：**
```python
class PaymentProcessor:
    def process_payment(self, payment_type: str, amount: float):
        if payment_type == "credit_card":
            # クレジットカード処理
            pass
        elif payment_type == "paypal":
            # PayPal 処理
            pass
        elif payment_type == "bitcoin":
            # 新しい支払い方法を追加するたびに、この関数を修正する必要がある
            pass
```

**良い例：**
```python
from abc import ABC, abstractmethod

class PaymentMethod(ABC):
    @abstractmethod
    def process(self, amount: float):
        pass

class CreditCardPayment(PaymentMethod):
    def process(self, amount: float):
        # クレジットカード処理
        pass

class PayPalPayment(PaymentMethod):
    def process(self, amount: float):
        # PayPal 処理
        pass

class BitcoinPayment(PaymentMethod):
    def process(self, amount: float):
        # Bitcoin 処理
        pass

class PaymentProcessor:
    def process_payment(self, payment_method: PaymentMethod, amount: float):
        payment_method.process(amount)
```

**チェックポイント：**
- 新機能追加時に既存コードを変更する必要があるか
- if-else の連鎖が長く続いていないか
- 抽象化やインターフェースを使用しているか

---

### 3. Liskov Substitution Principle（リスコフの置換原則）

**定義：** 派生型は、その基本型と置換可能でなければならない。サブクラスは親クラスの振る舞いを変えてはいけない。

**悪い例：**
```swift
class Rectangle {
    var width: Double
    var height: Double

    init(width: Double, height: Double) {
        self.width = width
        self.height = height
    }

    func area() -> Double {
        return width * height
    }
}

class Square: Rectangle {
    init(side: Double) {
        super.init(width: side, height: side)
    }

    // 正方形は幅と高さが同じでなければならない
    override var width: Double {
        didSet { height = width }
    }

    override var height: Double {
        didSet { width = height }
    }
}

// 問題：Rectangle を期待するコードが Square で動作しない
func testRectangle(rect: Rectangle) {
    rect.width = 5
    rect.height = 10
    assert(rect.area() == 50) // Square の場合、この assertion が失敗する
}
```

**良い例：**
```swift
protocol Shape {
    func area() -> Double
}

class Rectangle: Shape {
    let width: Double
    let height: Double

    init(width: Double, height: Double) {
        self.width = width
        self.height = height
    }

    func area() -> Double {
        return width * height
    }
}

class Square: Shape {
    let side: Double

    init(side: Double) {
        self.side = side
    }

    func area() -> Double {
        return side * side
    }
}
```

**チェックポイント：**
- サブクラスが親クラスの事前条件を強化していないか
- サブクラスが親クラスの事後条件を弱めていないか
- 親クラスの不変条件がサブクラスで保持されているか

---

### 4. Interface Segregation Principle（インターフェース分離の原則）

**定義：** クライアントは、自分が使わないメソッドに依存することを強制されるべきではない。

**悪い例：**
```java
interface Worker {
    void work();
    void eat();
    void sleep();
}

class HumanWorker implements Worker {
    public void work() { /* 作業する */ }
    public void eat() { /* 食事する */ }
    public void sleep() { /* 睡眠する */ }
}

class RobotWorker implements Worker {
    public void work() { /* 作業する */ }
    public void eat() { /* ロボットは食事しない - 空実装 */ }
    public void sleep() { /* ロボットは睡眠しない - 空実装 */ }
}
```

**良い例：**
```java
interface Workable {
    void work();
}

interface Eatable {
    void eat();
}

interface Sleepable {
    void sleep();
}

class HumanWorker implements Workable, Eatable, Sleepable {
    public void work() { /* 作業する */ }
    public void eat() { /* 食事する */ }
    public void sleep() { /* 睡眠する */ }
}

class RobotWorker implements Workable {
    public void work() { /* 作業する */ }
}
```

**チェックポイント：**
- インターフェースに空実装のメソッドがないか
- インターフェースが持つメソッドが多すぎないか
- クライアントが使わないメソッドに依存していないか

---

### 5. Dependency Inversion Principle（依存性逆転の原則）

**定義：** 上位モジュールは下位モジュールに依存してはならない。両方とも抽象に依存すべき。抽象は詳細に依存してはならない。詳細が抽象に依存すべき。

**悪い例：**
```typescript
class MySQLDatabase {
  save(data: string) {
    console.log("Saving to MySQL:", data);
  }
}

class UserService {
  private database: MySQLDatabase;

  constructor() {
    this.database = new MySQLDatabase(); // 具象クラスに直接依存
  }

  saveUser(user: string) {
    this.database.save(user);
  }
}
```

**良い例：**
```typescript
interface Database {
  save(data: string): void;
}

class MySQLDatabase implements Database {
  save(data: string) {
    console.log("Saving to MySQL:", data);
  }
}

class MongoDatabase implements Database {
  save(data: string) {
    console.log("Saving to MongoDB:", data);
  }
}

class UserService {
  private database: Database;

  constructor(database: Database) { // 抽象に依存
    this.database = database;
  }

  saveUser(user: string) {
    this.database.save(user);
  }
}

// 使用例
const mysqlDb = new MySQLDatabase();
const userService = new UserService(mysqlDb);
```

**チェックポイント：**
- 具象クラスに直接依存していないか
- 依存性注入（Dependency Injection）を使用しているか
- 抽象（インターフェース、抽象クラス）を通じて依存しているか

---

## DRY（Don't Repeat Yourself）

**定義：** 同じコードや知識を複数箇所に重複させない。

**悪い例：**
```go
func calculateCircleArea(radius float64) float64 {
    return 3.14159 * radius * radius
}

func calculateCircleCircumference(radius float64) float64 {
    return 2 * 3.14159 * radius
}

func calculateSphereVolume(radius float64) float64 {
    return (4.0 / 3.0) * 3.14159 * radius * radius * radius
}
```

**良い例：**
```go
const Pi = 3.14159265358979323846

func calculateCircleArea(radius float64) float64 {
    return Pi * radius * radius
}

func calculateCircleCircumference(radius float64) float64 {
    return 2 * Pi * radius
}

func calculateSphereVolume(radius float64) float64 {
    return (4.0 / 3.0) * Pi * radius * radius * radius
}
```

**より良い例（共通ロジックの抽出）：**
```python
def validate_email(email: str) -> bool:
    """メールアドレスの検証"""
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def register_user(email: str, password: str):
    if not validate_email(email):
        raise ValueError("Invalid email")
    # ユーザー登録処理

def send_invitation(email: str):
    if not validate_email(email):
        raise ValueError("Invalid email")
    # 招待メール送信処理

def update_email(user_id: int, new_email: str):
    if not validate_email(new_email):
        raise ValueError("Invalid email")
    # メールアドレス更新処理
```

**チェックポイント：**
- 同じコードブロックが複数箇所にコピーされていないか
- マジックナンバー（数値リテラル）が複数箇所で使われていないか
- 同じ検証ロジックが重複していないか
- 共通の処理を関数やメソッドとして抽出できないか

---

## KISS（Keep It Simple, Stupid）

**定義：** システムはできるだけシンプルに保つべき。不必要な複雑さを避ける。

**悪い例：**
```rust
// 過度に複雑な実装
fn is_even(n: i32) -> bool {
    match n {
        n if n % 2 == 0 => match n {
            n if n > 0 => true,
            n if n < 0 => true,
            _ => true,
        },
        _ => false,
    }
}
```

**良い例：**
```rust
fn is_even(n: i32) -> bool {
    n % 2 == 0
}
```

**悪い例（過度な抽象化）：**
```java
interface AnimalFactory {
    Animal createAnimal();
}

interface Animal {
    void makeSound();
}

class DogFactory implements AnimalFactory {
    public Animal createAnimal() {
        return new Dog();
    }
}

class Dog implements Animal {
    public void makeSound() {
        System.out.println("Woof!");
    }
}

// 使用例
AnimalFactory factory = new DogFactory();
Animal dog = factory.createAnimal();
dog.makeSound();
```

**良い例（必要な抽象化のみ）：**
```java
class Dog {
    public void makeSound() {
        System.out.println("Woof!");
    }
}

// 使用例
Dog dog = new Dog();
dog.makeSound();
```

**チェックポイント：**
- ネストが3階層以上深くなっていないか
- より簡潔に書ける方法がないか
- 現時点で必要のない抽象化をしていないか
- コードの意図が一目で理解できるか

---

## YAGNI（You Aren't Gonna Need It）

**定義：** 実際に必要になるまで機能を実装しない。将来必要になるかもしれない機能を先回りして実装しない。

**悪い例：**
```typescript
class User {
  constructor(
    public id: string,
    public name: string,
    public email: string,
    // 将来必要かもしれないフィールド
    public phoneNumber?: string,
    public address?: string,
    public dateOfBirth?: Date,
    public socialSecurityNumber?: string,
    public preferences?: UserPreferences,
    public metadata?: Map<string, any>
  ) {}

  // 現在使われていないメソッド
  updatePhoneNumber(phone: string) { /* ... */ }
  updateAddress(address: string) { /* ... */ }
  calculateAge() { /* ... */ }
  exportToXML() { /* ... */ }
  exportToJSON() { /* ... */ }
  exportToCSV() { /* ... */ }
}
```

**良い例：**
```typescript
class User {
  constructor(
    public id: string,
    public name: string,
    public email: string
  ) {}

  // 現在必要なメソッドのみ
  updateEmail(email: string) {
    this.email = email;
  }
}

// 必要になったら拡張する
```

**チェックポイント：**
- 現在使われていない機能がないか
- 「将来必要になるかもしれない」という理由だけで追加された機能がないか
- 未使用のパラメータやフィールドがないか
- 過度に汎用的な設計になっていないか

---

## 関心の分離（Separation of Concerns）

**定義：** プログラムを異なる関心事（concern）に分割し、それぞれが独立して変更可能であるようにする。

**悪い例：**
```python
def create_user_and_send_email(name, email, password):
    # データ検証
    if not email or '@' not in email:
        raise ValueError("Invalid email")

    # パスワードハッシュ化
    import hashlib
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # データベース保存
    import sqlite3
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users VALUES (?, ?, ?)",
                   (name, email, hashed_password))
    conn.commit()
    conn.close()

    # メール送信
    import smtplib
    server = smtplib.SMTP('smtp.example.com', 587)
    server.login('admin@example.com', 'password')
    message = f"Welcome {name}!"
    server.sendmail('admin@example.com', email, message)
    server.quit()

    # ログ記録
    import logging
    logging.info(f"User {name} created and notified")
```

**良い例：**
```python
# データ検証の関心
class UserValidator:
    @staticmethod
    def validate_email(email: str) -> bool:
        return email and '@' in email

    @staticmethod
    def validate_password(password: str) -> bool:
        return len(password) >= 8

# パスワード処理の関心
class PasswordHasher:
    @staticmethod
    def hash(password: str) -> str:
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()

# データ永続化の関心
class UserRepository:
    def save(self, name: str, email: str, hashed_password: str):
        import sqlite3
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users VALUES (?, ?, ?)",
                       (name, email, hashed_password))
        conn.commit()
        conn.close()

# メール送信の関心
class EmailService:
    def send_welcome_email(self, email: str, name: str):
        import smtplib
        server = smtplib.SMTP('smtp.example.com', 587)
        server.login('admin@example.com', 'password')
        message = f"Welcome {name}!"
        server.sendmail('admin@example.com', email, message)
        server.quit()

# ログ記録の関心
class Logger:
    @staticmethod
    def log_user_creation(name: str):
        import logging
        logging.info(f"User {name} created and notified")

# オーケストレーション
class UserService:
    def __init__(self, validator, hasher, repository, email_service, logger):
        self.validator = validator
        self.hasher = hasher
        self.repository = repository
        self.email_service = email_service
        self.logger = logger

    def create_user(self, name: str, email: str, password: str):
        if not self.validator.validate_email(email):
            raise ValueError("Invalid email")

        hashed_password = self.hasher.hash(password)
        self.repository.save(name, email, hashed_password)
        self.email_service.send_welcome_email(email, name)
        self.logger.log_user_creation(name)
```

**チェックポイント：**
- 1つの関数/クラスが複数の異なる関心事を扱っていないか
- ビジネスロジックと UI が混在していないか
- データアクセスロジックがビジネスロジックと分離されているか

---

## コンポジション vs 継承

**原則：** 継承よりもコンポジションを優先する。

**継承の問題点：**
- 強い結合（tight coupling）
- 親クラスの変更が子クラスに影響
- 多重継承の問題（言語によっては不可）

**悪い例（継承の乱用）：**
```java
class Vehicle {
    void start() { /* ... */ }
    void stop() { /* ... */ }
}

class Car extends Vehicle {
    void openTrunk() { /* ... */ }
}

class ElectricCar extends Car {
    void charge() { /* ... */ }
}

// 問題：バイクを追加したい場合、Car を継承できない
```

**良い例（コンポジション）：**
```java
interface Engine {
    void start();
    void stop();
}

class GasEngine implements Engine {
    public void start() { /* ガソリンエンジン始動 */ }
    public void stop() { /* ガソリンエンジン停止 */ }
}

class ElectricEngine implements Engine {
    public void start() { /* 電気モーター始動 */ }
    public void stop() { /* 電気モーター停止 */ }

    void charge() { /* 充電 */ }
}

class Vehicle {
    private Engine engine;

    Vehicle(Engine engine) {
        this.engine = engine;
    }

    void start() {
        engine.start();
    }

    void stop() {
        engine.stop();
    }
}

// 使用例
Vehicle gasCar = new Vehicle(new GasEngine());
Vehicle electricCar = new Vehicle(new ElectricEngine());
```

**チェックポイント：**
- 継承階層が3階層以上深くなっていないか
- 「is-a」関係ではなく「has-a」関係で表現できないか
- コンポジションで代替できないか

---

## 早期リターン（Early Return）

**定義：** エラーケースや特殊ケースを早期に return することで、ネストを浅く保つ。

**悪い例：**
```javascript
function processOrder(order) {
  if (order) {
    if (order.items.length > 0) {
      if (order.customer) {
        if (order.customer.hasValidPayment) {
          // 実際の処理
          return calculateTotal(order);
        } else {
          throw new Error("Invalid payment method");
        }
      } else {
        throw new Error("Customer not found");
      }
    } else {
      throw new Error("Order has no items");
    }
  } else {
    throw new Error("Order is null");
  }
}
```

**良い例：**
```javascript
function processOrder(order) {
  if (!order) {
    throw new Error("Order is null");
  }

  if (order.items.length === 0) {
    throw new Error("Order has no items");
  }

  if (!order.customer) {
    throw new Error("Customer not found");
  }

  if (!order.customer.hasValidPayment) {
    throw new Error("Invalid payment method");
  }

  // 実際の処理
  return calculateTotal(order);
}
```

**チェックポイント：**
- ネストが深くなっていないか
- エラーケースを先に処理しているか
- メインの処理ロジックが明確か

---

## ガード節（Guard Clauses）

**定義：** 関数の先頭で前提条件をチェックし、満たされない場合は早期に return する。

**悪い例：**
```swift
func calculateDiscount(price: Double, customerType: String) -> Double {
    var discount = 0.0

    if price > 0 {
        if customerType == "premium" {
            discount = price * 0.2
        } else if customerType == "regular" {
            discount = price * 0.1
        } else if customerType == "new" {
            discount = price * 0.05
        }
    }

    return discount
}
```

**良い例：**
```swift
func calculateDiscount(price: Double, customerType: String) -> Double {
    // ガード節
    guard price > 0 else {
        return 0.0
    }

    // メインロジック
    switch customerType {
    case "premium":
        return price * 0.2
    case "regular":
        return price * 0.1
    case "new":
        return price * 0.05
    default:
        return 0.0
    }
}
```

**チェックポイント：**
- 前提条件を関数の先頭でチェックしているか
- 不正な入力に対して早期に return しているか
- ガード節を使うことでメインロジックが明確になっているか

---

## まとめ

これらの原則は絶対的なルールではなく、ガイドラインです。コンテキストに応じて適切に適用することが重要です。

- **バランス**：すべての原則を完璧に適用しようとすると、過度に複雑になることがある
- **実用性**：小規模なスクリプトやプロトタイプでは、一部の原則を緩和しても良い
- **チーム合意**：チームで合意されたコーディング規約を優先する
- **段階的改善**：既存のコードを一度にすべて書き直すのではなく、段階的に改善する
