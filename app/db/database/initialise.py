from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from app.db.database.base import Base
from app.db.database.session import engine
from app.db.models.pizza import Pizza
from app.db.models.size import Size
from app.db.models.topping import Topping
from app.config import settings

def create_database() -> None:
    """Create the database if it doesn't exist"""
    default_engine = create_engine(settings.SQLALCHEMY_DATABASE_URI.replace('/pizza', '/postgres'))
    conn = default_engine.connect()
    conn.execute(text("COMMIT"))
    try:
        conn.execute(text("CREATE DATABASE pizza"))
    except Exception:
        pass
    finally:
        conn.close()

def initialise(db: Session) -> None:
    """Initialize database with tables and initial data"""
    try:
        # Try to create tables
        Base.metadata.create_all(bind=engine)
    except OperationalError:
        # If database doesn't exist, create it
        create_database()
        Base.metadata.create_all(bind=engine)
    print("Database initialised", db.query(Size).first())
    # Add initial data if tables are empty
    if not db.query(Size).first():
        sizes = [
            Size(name="Small", multiplier=1.0),
            Size(name="Medium", multiplier=1.5),
            Size(name="Large", multiplier=2.0),
        ]
        db.add_all(sizes)
    
    if not db.query(Pizza).first():
        pizzas = [
            Pizza(
                name="Margherita",
                description="Fresh tomatoes, mozzarella, basil",
                base_price=10.0,
                image='https://images.unsplash.com/photo-1604068549290-dea0e4a305ca?w=800&auto=format&fit=crop'
            ),
            Pizza(
                name="Pepperoni",
                description="Pepperoni, cheese, tomato sauce",
                base_price=12.0,
                image='https://images.unsplash.com/photo-1628840042765-356cda07504e?w=800&auto=format&fit=crop'
            ),
            Pizza(
                name="Veggie Supreme",
                description='Bell peppers, mushrooms, onions, olives, and tomatoes',
                base_price=11.0,
                image='https://images.unsplash.com/photo-1571066811602-716dc70c3644?w=800&auto=format&fit=crop'
            ),
            Pizza(
                name="BBQ Chicken",
                description='Grilled chicken, BBQ sauce, red onions, and cilantro',
                base_price=13.0,
                image='https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&auto=format&fit=crop'
            ),
        ]
        db.add_all(pizzas)
    
    if not db.query(Topping).first():
        toppings = [
            Topping(name="Extra Cheese", price=2.0, icon="🧀"),
            Topping(name="Mushrooms", price=1.5, icon="🍄"),
            Topping(name="Olives", price=1.0, icon="🫒"),
            Topping(name="Pepperoni", price=2.5, icon="🍖"),
            Topping(name="Onions", price=1.0, icon="🧅"),
        ]
        db.add_all(toppings)
    
    db.commit()
    pass
