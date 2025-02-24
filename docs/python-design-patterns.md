# Python Design Patterns - A Comprehensive Guide

## Table of Contents

- [Python Design Patterns - A Comprehensive Guide](#python-design-patterns---a-comprehensive-guide)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Creational Patterns](#creational-patterns)
    - [1. Singleton](#1-singleton)
    - [2. Factory Method](#2-factory-method)
    - [3. Abstract Factory](#3-abstract-factory)
    - [4. Builder](#4-builder)
    - [5. Prototype](#5-prototype)
  - [Structural Patterns](#structural-patterns)
    - [1. Adapter](#1-adapter)
    - [2. Bridge](#2-bridge)
    - [3. Composite](#3-composite)
    - [4. Decorator](#4-decorator)
    - [5. Facade](#5-facade)
    - [6. Flyweight](#6-flyweight)
    - [7. Proxy](#7-proxy)
  - [Behavioral Patterns](#behavioral-patterns)
    - [1. Chain of Responsibility](#1-chain-of-responsibility)
    - [2. Command](#2-command)
    - [3. Interpreter](#3-interpreter)
    - [4. Iterator](#4-iterator)
    - [5. Mediator](#5-mediator)
    - [6. Memento](#6-memento)
    - [7. Observer](#7-observer)
    - [8. State](#8-state)
    - [9. Strategy](#9-strategy)
    - [10. Template Method](#10-template-method)
    - [11. Visitor](#11-visitor)
  - [Conclusion](#conclusion)

---

## Introduction

Design patterns are **reusable solutions** to common software design problems. They provide templates for solving recurring challenges related to object creation, structure, and behavior. While the principles behind these patterns transcend specific programming languages, Python's dynamic features (like **first-class functions**, **duck typing**, **metaprogramming**) offer unique and often simpler ways to implement them.

This document groups patterns into three categories:

- **Creational**: Object creation mechanisms and abstractions.  
- **Structural**: Ways to compose classes or objects for new functionalities.  
- **Behavioral**: Patterns that define communication between objects, distributing responsibilities.

---

## Creational Patterns

Creational patterns focus on how to instantiate objects in a flexible and reusable way.

### 1. Singleton

**Intent**: Ensure a class has only one instance and provide a global point of access to it.

**Motivation**:  

- Sometimes you need exactly one instance of a class, e.g., a database connection pool, a logger, or a configuration manager.

**Implementation Approach (Python)**:

- A commonly used (though not the only) approach is to store the singleton instance in a module-level variable.

```python
# singleton_example.py

class SingletonMeta(type):
    """A thread-safe implementation of a Singleton metaclass."""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class Logger(metaclass=SingletonMeta):
    def __init__(self):
        # This constructor is called only once
        self.log_file = "app.log"

    def write_log(self, message: str):
        with open(self.log_file, "a") as f:
            f.write(message + "\n")

# Usage
logger1 = Logger()
logger2 = Logger()
print(logger1 is logger2)  # True
```

**Pros**:

- Controlled access to a single instance.  
- Lazy initialization if desired.

**Cons**:

- Can introduce global state, which can complicate testing.  
- Limits flexibility in large applications.

---

### 2. Factory Method

**Intent**: Define an interface for creating an object, but let subclasses decide which class to instantiate.

**Motivation**:  

- If you have a base class with multiple possible subclasses, the factory method pattern defers subclass choice to child classes.

```python
from abc import ABC, abstractmethod

class Button(ABC):
    @abstractmethod
    def render(self):
        pass

class HTMLButton(Button):
    def render(self):
        return "<button>HTML Button</button>"

class WindowsButton(Button):
    def render(self):
        return "Windows Button"

class Dialog(ABC):
    """Factory Method is the 'create_button' here."""
    @abstractmethod
    def create_button(self) -> Button:
        pass

    def render_dialog(self):
        button = self.create_button()
        print("Dialog renders:", button.render())

class HTMLDialog(Dialog):
    def create_button(self) -> Button:
        return HTMLButton()

class WindowsDialog(Dialog):
    def create_button(self) -> Button:
        return WindowsButton()

# Usage
dialog_type = "html"
if dialog_type == "html":
    dialog = HTMLDialog()
else:
    dialog = WindowsDialog()

dialog.render_dialog()
```

**Pros**:

- Creates objects without exposing the creation logic.  
- Adheres to **Open/Closed Principle** (extensible without modifying existing code).

**Cons**:

- Can lead to additional subclassing or overhead for simple object creation scenarios.

---

### 3. Abstract Factory

**Intent**: Provide an interface for creating **families** of related or dependent objects without specifying their concrete classes.

**Motivation**:

- Useful when multiple products (objects) must work together but differ in families, e.g., cross-platform UI elements.

```python
from abc import ABC, abstractmethod

# Products: Chair and Sofa
class Chair(ABC):
    @abstractmethod
    def sit_on(self):
        pass

class VictorianChair(Chair):
    def sit_on(self):
        print("Sitting on a Victorian Chair")

class ModernChair(Chair):
    def sit_on(self):
        print("Sitting on a Modern Chair")

class Sofa(ABC):
    @abstractmethod
    def lie_on(self):
        pass

class VictorianSofa(Sofa):
    def lie_on(self):
        print("Lying on a Victorian Sofa")

class ModernSofa(Sofa):
    def lie_on(self):
        print("Lying on a Modern Sofa")

# Abstract Factory
class FurnitureFactory(ABC):
    @abstractmethod
    def create_chair(self) -> Chair:
        pass

    @abstractmethod
    def create_sofa(self) -> Sofa:
        pass

# Concrete Factories
class VictorianFurnitureFactory(FurnitureFactory):
    def create_chair(self) -> Chair:
        return VictorianChair()

    def create_sofa(self) -> Sofa:
        return VictorianSofa()

class ModernFurnitureFactory(FurnitureFactory):
    def create_chair(self) -> Chair:
        return ModernChair()

    def create_sofa(self) -> Sofa:
        return ModernSofa()

# Usage
def furnish_apartment(factory: FurnitureFactory):
    chair = factory.create_chair()
    sofa = factory.create_sofa()
    chair.sit_on()
    sofa.lie_on()

furnish_apartment(VictorianFurnitureFactory())
furnish_apartment(ModernFurnitureFactory())
```

**Pros**:

- Ensures that products from the same family are used consistently.  
- Avoids incompatible objects.

**Cons**:

- Complex to add new product families; requires updating the interface.

---

### 4. Builder

**Intent**: Separate the construction of a complex object from its representation so that the same construction process can create different representations.

**Motivation**:

- Constructing complex objects step by step (e.g., building a complex PDF document with metadata, table of contents, chapters, etc.).

```python
from abc import ABC, abstractmethod

# Product
class House:
    def __init__(self):
        self.foundation = None
        self.structure = None
        self.roof = None
        self.rooms = []

class HouseBuilder(ABC):
    @abstractmethod
    def build_foundation(self):
        pass

    @abstractmethod
    def build_structure(self):
        pass

    @abstractmethod
    def build_roof(self):
        pass

    @abstractmethod
    def add_rooms(self):
        pass

    @abstractmethod
    def get_result(self) -> House:
        pass

class ConcreteHouseBuilder(HouseBuilder):
    def __init__(self):
        self.house = House()

    def build_foundation(self):
        self.house.foundation = "Concrete Slab"

    def build_structure(self):
        self.house.structure = "Concrete and Steel"

    def build_roof(self):
        self.house.roof = "Concrete Slab Roof"

    def add_rooms(self):
        self.house.rooms = ["Living Room", "Kitchen", "Bedroom", "Bathroom"]

    def get_result(self) -> House:
        return self.house

class Director:
    """Orchestrates the construction steps."""
    def __init__(self, builder: HouseBuilder):
        self._builder = builder

    def construct_simple_house(self):
        self._builder.build_foundation()
        self._builder.build_structure()
        self._builder.build_roof()
        self._builder.add_rooms()

# Usage
builder = ConcreteHouseBuilder()
director = Director(builder)
director.construct_simple_house()
house = builder.get_result()
print(house.foundation, house.rooms)  # "Concrete Slab", [...]
```

---

### 5. Prototype

**Intent**: Specify the kinds of objects to create using a prototypical instance, and create new objects by copying this prototype.

**Motivation**:

- When direct object construction is expensive, you can clone a prototype instead of building from scratch.

**Implementation**:

- In Python, you can rely on the `copy` or `deepcopy` module.

```python
import copy

class Prototype:
    def __init__(self, name, nested_data):
        self.name = name
        self.nested_data = nested_data

    def clone(self):
        return copy.deepcopy(self)

# Usage
original = Prototype("Prototype1", {"numbers": [1, 2, 3]})
clone_obj = original.clone()
```

---

## Structural Patterns

### 1. Adapter

**Intent**: Convert the interface of a class into another interface clients expect. Adapter lets classes work together that could not otherwise because of incompatible interfaces.

```python
class FahrenheitThermometer:
    def get_temperature_f(self):
        return 75.0

class CelsiusThermometerAdapter:
    def __init__(self, fahrenheit_thermometer):
        self._therm = fahrenheit_thermometer

    def get_temperature_c(self):
        f = self._therm.get_temperature_f()
        return (f - 32) * 5 / 9

# Usage
fahrenheit = FahrenheitThermometer()
adapter = CelsiusThermometerAdapter(fahrenheit)
print(adapter.get_temperature_c())
```

---

### 2. Bridge

**Intent**: Decouple an abstraction from its implementation so that the two can vary independently.

**Motivation**:

- When dealing with multiple dimensions of variation (e.g., shapes + different rendering APIs), the Bridge pattern splits them into separate class hierarchies.

```python
from abc import ABC, abstractmethod

# Implementor
class DrawingAPI(ABC):
    @abstractmethod
    def draw_circle(self, x, y, radius):
        pass

class DrawingAPI1(DrawingAPI):
    def draw_circle(self, x, y, radius):
        print(f"[API1] Circle at {x}:{y} radius {radius}")

class DrawingAPI2(DrawingAPI):
    def draw_circle(self, x, y, radius):
        print(f"[API2] Circle at {x}:{y} radius {radius}")

# Abstraction
class Shape(ABC):
    def __init__(self, drawing_api: DrawingAPI):
        self._drawing_api = drawing_api

    @abstractmethod
    def draw(self):
        pass

class CircleShape(Shape):
    def __init__(self, x, y, radius, drawing_api: DrawingAPI):
        super().__init__(drawing_api)
        self.x = x
        self.y = y
        self.radius = radius

    def draw(self):
        self._drawing_api.draw_circle(self.x, self.y, self.radius)

# Usage
circle1 = CircleShape(1, 2, 3, DrawingAPI1())
circle2 = CircleShape(5, 7, 11, DrawingAPI2())
circle1.draw()
circle2.draw()
```

---

### 3. Composite

**Intent**: Compose objects into tree structures. Allows clients to treat individual objects and compositions of objects uniformly.

```python
class Component:
    def operation(self):
        pass

class Leaf(Component):
    def __init__(self, name):
        self.name = name

    def operation(self):
        print(f"Leaf: {self.name}")

class Composite(Component):
    def __init__(self):
        self.children = []

    def add(self, component: Component):
        self.children.append(component)

    def operation(self):
        for child in self.children:
            child.operation()

# Usage
root = Composite()
root.add(Leaf("Leaf1"))
child_tree = Composite()
child_tree.add(Leaf("Leaf2"))
root.add(child_tree)
root.operation()
```

---

### 4. Decorator

**Intent**: Attach additional responsibilities to an object dynamically. Decorators provide a flexible alternative to subclassing for extending functionality.

```python
class Coffee:
    def cost(self):
        return 2.0

class CoffeeDecorator:
    def __init__(self, coffee):
        self._coffee = coffee

    def cost(self):
        return self._coffee.cost()

class MilkDecorator(CoffeeDecorator):
    def cost(self):
        return self._coffee.cost() + 0.5

class SugarDecorator(CoffeeDecorator):
    def cost(self):
        return self._coffee.cost() + 0.2

# Usage
basic_coffee = Coffee()
coffee_with_milk = MilkDecorator(basic_coffee)
coffee_with_milk_sugar = SugarDecorator(coffee_with_milk)
print(coffee_with_milk_sugar.cost())  # 2.7
```

---

### 5. Facade

**Intent**: Provide a unified interface to a set of interfaces in a subsystem. Facade defines a higher-level interface that makes the subsystem easier to use.

```python
class OrderSubsystem:
    def place_order(self, product_id):
        print(f"Order placed for product {product_id}")

class PaymentSubsystem:
    def process_payment(self, product_id):
        print(f"Payment processed for product {product_id}")

class ShippingSubsystem:
    def ship_product(self, product_id):
        print(f"Shipped product {product_id}")

class ECommerceFacade:
    def __init__(self):
        self.order = OrderSubsystem()
        self.payment = PaymentSubsystem()
        self.shipping = ShippingSubsystem()

    def purchase(self, product_id):
        self.order.place_order(product_id)
        self.payment.process_payment(product_id)
        self.shipping.ship_product(product_id)

# Usage
facade = ECommerceFacade()
facade.purchase(101)
```

---

### 6. Flyweight

**Intent**: Use sharing to support large numbers of fine-grained objects efficiently.

```python
class FlyweightFactory:
    _flyweights = {}

    @classmethod
    def get_flyweight(cls, key):
        if key not in cls._flyweights:
            cls._flyweights[key] = SomeHeavyObject(key)
        return cls._flyweights[key]

class SomeHeavyObject:
    def __init__(self, intrinsic_state):
        self.intrinsic_state = intrinsic_state
        # Potentially heavy data

# Usage
fw1 = FlyweightFactory.get_flyweight("state1")
fw2 = FlyweightFactory.get_flyweight("state1")
assert fw1 is fw2
```

---

### 7. Proxy

**Intent**: Provide a surrogate or placeholder for another object to control access to it.

```python
class RealService:
    def request(self):
        print("RealService handling request")

class ProxyService:
    def __init__(self):
        self._real_service = RealService()
        self._is_authenticated = False

    def authenticate(self):
        self._is_authenticated = True

    def request(self):
        if self._is_authenticated:
            self._real_service.request()
        else:
            print("Access Denied. Please authenticate first.")

# Usage
proxy = ProxyService()
proxy.request()  # Denied
proxy.authenticate()
proxy.request()  # RealService handling request
```

---

## Behavioral Patterns

### 1. Chain of Responsibility

**Intent**: Pass requests along a chain of handlers. Each handler decides either to process the request or to pass it to the next handler.

```python
class Handler:
    def __init__(self, successor=None):
        self._successor = successor

    def handle(self, request):
        if self._successor:
            self._successor.handle(request)

class ConcreteHandler1(Handler):
    def handle(self, request):
        if request < 10:
            print(f"Handler1 handled request {request}")
        else:
            super().handle(request)

class ConcreteHandler2(Handler):
    def handle(self, request):
        if request < 20:
            print(f"Handler2 handled request {request}")
        else:
            super().handle(request)

# Usage
h1 = ConcreteHandler1(ConcreteHandler2())
h1.handle(5)
h1.handle(15)
h1.handle(25)  # Not handled
```

---

### 2. Command

**Intent**: Encapsulate a request as an object, thereby letting you parametrize clients with different requests, queue or log requests, and support undo operations.

```python
class Command:
    def execute(self):
        pass

class Receiver:
    def action(self):
        print("Receiver action")

class ConcreteCommand(Command):
    def __init__(self, receiver: Receiver):
        self._receiver = receiver

    def execute(self):
        self._receiver.action()

class Invoker:
    def __init__(self):
        self._commands = []

    def store_command(self, command):
        self._commands.append(command)

    def execute_commands(self):
        for cmd in self._commands:
            cmd.execute()

# Usage
recv = Receiver()
cmd = ConcreteCommand(recv)
invoker = Invoker()
invoker.store_command(cmd)
invoker.execute_commands()
```

---

### 3. Interpreter

**Intent**: Given a language, define a representation for its grammar along with an interpreter that uses the representation to interpret sentences in the language.

**Example** (simplified for demonstration):

```python
class AbstractExpression:
    def interpret(self, context):
        pass

class NumberExpression(AbstractExpression):
    def __init__(self, number):
        self.number = number

    def interpret(self, context):
        return int(self.number)

class AddExpression(AbstractExpression):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def interpret(self, context):
        return self.left.interpret(context) + self.right.interpret(context)

# Usage
# expression "5 + 7"
expr = AddExpression(NumberExpression("5"), NumberExpression("7"))
result = expr.interpret(None)  # 12
```

---

### 4. Iterator

**Intent**: Provide a way to access the elements of an aggregate object sequentially without exposing its underlying representation.

```python
class CustomCollection:
    def __init__(self, items):
        self.items = items

    def __iter__(self):
        return CustomIterator(self.items)

class CustomIterator:
    def __init__(self, items):
        self._items = items
        self._index = 0

    def __next__(self):
        if self._index >= len(self._items):
            raise StopIteration
        result = self._items[self._index]
        self._index += 1
        return result

# Usage
collection = CustomCollection([1, 2, 3])
for item in collection:
    print(item)
```

---

### 5. Mediator

**Intent**: Define an object that encapsulates how a set of objects interact. Mediator promotes loose coupling by preventing objects from referring to each other explicitly.

```python
class Mediator:
    def notify(self, sender, event):
        pass

class ConcreteMediator(Mediator):
    def __init__(self, component1, component2):
        self.component1 = component1
        self.component1.mediator = self
        self.component2 = component2
        self.component2.mediator = self

    def notify(self, sender, event):
        if event == "A":
            print("Mediator reacts on A and triggers B")
            self.component2.do_b()
        elif event == "B":
            print("Mediator reacts on B and triggers A")
            self.component1.do_a()

class BaseComponent:
    def __init__(self, mediator=None):
        self.mediator = mediator

class Component1(BaseComponent):
    def do_a(self):
        print("Component1 does A")
        self.mediator.notify(self, "A")

class Component2(BaseComponent):
    def do_b(self):
        print("Component2 does B")
        self.mediator.notify(self, "B")

# Usage
c1 = Component1()
c2 = Component2()
mediator = ConcreteMediator(c1, c2)
c1.do_a()
```

---

### 6. Memento

**Intent**: Capture and externalize an object's internal state so that the object can be restored to this state later.

```python
class Memento:
    def __init__(self, state):
        self._state = state

    def get_saved_state(self):
        return self._state

class Originator:
    def __init__(self):
        self._state = None

    def set_state(self, state):
        self._state = state

    def save_to_memento(self):
        return Memento(self._state)

    def restore_from_memento(self, memento):
        self._state = memento.get_saved_state()

# Usage
originator = Originator()
originator.set_state("State1")
m1 = originator.save_to_memento()

originator.set_state("State2")
originator.restore_from_memento(m1)
```

---

### 7. Observer

**Intent**: Define a one-to-many dependency between objects so that when one object changes state, all its dependents are notified.

```python
class Subject:
    def __init__(self):
        self._observers = []
        self._state = None

    def attach(self, observer):
        self._observers.append(observer)

    def detach(self, observer):
        self._observers.remove(observer)

    def notify(self):
        for obs in self._observers:
            obs.update(self._state)

    def set_state(self, value):
        self._state = value
        self.notify()

class Observer:
    def update(self, new_state):
        pass

class ConcreteObserver(Observer):
    def update(self, new_state):
        print(f"Observer got state: {new_state}")

# Usage
subject = Subject()
obs = ConcreteObserver()
subject.attach(obs)
subject.set_state(10)
```

---

### 8. State

**Intent**: Allow an object to alter its behavior when its internal state changes. The object will appear to change its class.

```python
class State:
    def handle(self, context):
        pass

class ConcreteStateA(State):
    def handle(self, context):
        print("State A handling request, transitioning to B")
        context.state = ConcreteStateB()

class ConcreteStateB(State):
    def handle(self, context):
        print("State B handling request, transitioning to A")
        context.state = ConcreteStateA()

class Context:
    def __init__(self):
        self.state = ConcreteStateA()

    def request(self):
        self.state.handle(self)

# Usage
ctx = Context()
ctx.request()  # State A -> B
ctx.request()  # State B -> A
```

---

### 9. Strategy

**Intent**: Define a family of algorithms, encapsulate each one, and make them interchangeable. Strategy lets the algorithm vary independently from clients that use it.

```python
from abc import ABC, abstractmethod

class Strategy(ABC):
    @abstractmethod
    def do_operation(self, a, b):
        pass

class AddStrategy(Strategy):
    def do_operation(self, a, b):
        return a + b

class MultiplyStrategy(Strategy):
    def do_operation(self, a, b):
        return a * b

class Context:
    def __init__(self, strategy: Strategy):
        self._strategy = strategy

    def set_strategy(self, strategy: Strategy):
        self._strategy = strategy

    def execute_strategy(self, a, b):
        return self._strategy.do_operation(a, b)

# Usage
context = Context(AddStrategy())
print(context.execute_strategy(4, 5))  # 9
context.set_strategy(MultiplyStrategy())
print(context.execute_strategy(4, 5))  # 20
```

---

### 10. Template Method

**Intent**: Define the skeleton of an algorithm in an operation, deferring some steps to subclasses.

```python
from abc import ABC, abstractmethod

class Game(ABC):
    def play(self):
        self.init_game()
        self.start_play()
        self.end_play()

    @abstractmethod
    def init_game(self):
        pass

    @abstractmethod
    def start_play(self):
        pass

    @abstractmethod
    def end_play(self):
        pass

class Chess(Game):
    def init_game(self):
        print("Chess initialized")

    def start_play(self):
        print("Chess started")

    def end_play(self):
        print("Chess finished")

# Usage
chess = Chess()
chess.play()
```

---

### 11. Visitor

**Intent**: Represent an operation to be performed on the elements of an object structure. Visitor lets you define a new operation without changing the classes of the elements on which it operates.

```python
from abc import ABC, abstractmethod

class Visitor(ABC):
    @abstractmethod
    def visit_element_a(self, element):
        pass

    @abstractmethod
    def visit_element_b(self, element):
        pass

class Element(ABC):
    @abstractmethod
    def accept(self, visitor: Visitor):
        pass

class ConcreteElementA(Element):
    def accept(self, visitor: Visitor):
        visitor.visit_element_a(self)

class ConcreteElementB(Element):
    def accept(self, visitor: Visitor):
        visitor.visit_element_b(self)

class ConcreteVisitor(Visitor):
    def visit_element_a(self, element):
        print("Visitor visiting Element A")

    def visit_element_b(self, element):
        print("Visitor visiting Element B")

# Usage
elements = [ConcreteElementA(), ConcreteElementB()]
visitor = ConcreteVisitor()
for e in elements:
    e.accept(visitor)
```

---

## Conclusion

Understanding and applying these design patterns in Python can help you write **cleaner, more maintainable** code. Each pattern addresses a **common problem** in software design:

- **Creational** patterns handle object construction in flexible ways (e.g., `Singleton`, `Factory`, `Builder`).  
- **Structural** patterns help compose classes or objects (e.g., `Adapter`, `Decorator`, `Facade`).  
- **Behavioral** patterns manage object interactions and responsibilities (e.g., `Observer`, `Strategy`, `Visitor`).

Python’s dynamic features may simplify or slightly alter classical implementations found in languages like C++ or Java; yet, the **core intent** remains the same. Familiarity with design patterns ultimately enables you to **recognize common challenges** and **apply proven solutions**, making your code more robust and extensible.
