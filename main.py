from fasthtml.common import *
from dataclasses import dataclass
from datetime import datetime
import sqlite3
import os
import logging
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app, rt = fast_app()

# Database connection
DB_PATH = 'data/socks.db'

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS socks (
                sock_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sock_style TEXT NOT NULL,
                sock_hue TEXT NOT NULL,
                foot_hugger_size TEXT NOT NULL,
                last_adventure TEXT NOT NULL,
                sock_mood TEXT,
                superhero_rating INTEGER
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
        raise
    finally:
        conn.close()

init_db()

# Database setup
db = database(DB_PATH)
socks = db.t.socks
if socks not in db.t:
    socks.create(id=int, sock_style=str, sock_hue=str, foot_hugger_size=str, last_adventure=str, sock_mood=str, superhero_rating=int, pk='id')
Sock = socks.dataclass()

# Updated SOCK_STYLES with descriptions
SOCK_STYLES = {
    'Ankle': 'Low-cut socks that hit just above the ankle',
    'Crew': 'Classic mid-calf length socks',
    'Knee-High': 'Socks that extend to just below the knee',
    'No-Show': 'Ultra-low socks that are hidden in shoes',
    'Dress': 'Thin, formal socks for business or formal wear',
    'Athletic': 'Moisture-wicking socks for sports and exercise',
    'Compression': 'Tight-fitting socks that promote circulation',
    'Wool': 'Warm, natural fiber socks for cold weather'
}

# Predefined lists for sock attributes
SOCK_HUES = [
    ('⚫', 'Black'),
    ('⚪', 'White'),
    ('🔘', 'Gray'),
    ('🔵', 'Navy'),
    ('🟤', 'Brown'),
    ('🔴', 'Red'),
    ('🔵', 'Blue'),
    ('🟢', 'Green'),
    ('🟡', 'Yellow'),
    ('🟣', 'Purple'),
    ('🌸', 'Pink'),
    ('🟠', 'Orange')
]
FOOT_HUGGER_SIZES = [
    ('XS', 'Pixie Feet'),
    ('S', 'Nimble Toes'),
    ('M', 'Average Joe Soles'),
    ('L', 'Bigfoot Juniors'),
    ('XL', 'Sasquatch Specials'),
    ('XXL', 'Yeti Yacht Socks')
]
SOCK_MOODS = ['Happy', 'Sad', 'Excited', 'Relaxed', 'Energetic', 'Cozy']
SUPERHERO_RATINGS = list(range(1, 11))  # 1 to 10 rating scale

# Form validation
def validate_sock_form(style: str, hue: str, size: str, mood: str, superhero_rating: int) -> Optional[str]:
    if not style or not hue or not size or not mood or superhero_rating is None:
        return "All fields are required."
    if style not in SOCK_STYLES:
        return "Invalid sock style selected."
    if hue not in [color for _, color in SOCK_HUES]:
        return "Invalid sock hue selected."
    if size not in [s for s, _ in FOOT_HUGGER_SIZES]:
        return "Invalid sock size selected."
    if mood not in SOCK_MOODS:
        return "Invalid sock mood selected."
    if superhero_rating not in SUPERHERO_RATINGS:
        return "Invalid superhero rating selected."
    return None

# Updated sock_form function
def sock_form(sock: Optional[Sock] = None):
    return Form(method="post", action="/add_sock" if not sock else f"/edit/{sock.id}")(
        Fieldset(
            Label('Style', Select(name="style", required=True)(
                Option(value="", disabled=True, selected=not sock)("Select Style"),
                *(Option(value=style, selected=sock and sock.sock_style == style)(f"{style}: {description}") 
                  for style, description in SOCK_STYLES.items())
            )),
            Label('Hue', Select(name="hue", required=True)(
                Option(value="", disabled=True, selected=not sock)("Select Hue"),
                *(Option(value=color, selected=sock and sock.sock_hue == color)(f"{emoji} {color}") 
                  for emoji, color in SOCK_HUES)
            )),
            Label('Size', Select(name="size", required=True)(
                Option(value="", disabled=True, selected=not sock)("Select Size"),
                *(Option(value=size, selected=sock and sock.foot_hugger_size == size)(f"{size} - {description}") 
                  for size, description in FOOT_HUGGER_SIZES)
            )),
            Label('Mood', Select(name="mood", required=True)(
                Option(value="", disabled=True, selected=not sock)("Select Mood"),
                *(Option(value=mood, selected=sock and sock.sock_mood == mood)(mood) 
                  for mood in SOCK_MOODS)
            )),
            Label('Superhero Rating', Select(name="superhero_rating", required=True)(
                Option(value="", disabled=True, selected=not sock)("Select Rating"),
                *(Option(value=str(rating), selected=sock and sock.superhero_rating == rating)(str(rating)) 
                  for rating in SUPERHERO_RATINGS)
            )),
        ),
        Button("Save", type="submit"),
    )

def sock_list():
    try:
        sock_data = socks(order_by='id')
        if not sock_data:
            return P("Your sock drawer is empty. Add some socks to get started!")
        return Ul(*(
            Li(
                f"{sock.sock_style} - {next((emoji for emoji, color in SOCK_HUES if color == sock.sock_hue), '🧦')} {sock.sock_hue} - {sock.foot_hugger_size} - Last adventure: {sock.last_adventure} - Mood: {sock.sock_mood} - Superhero Rating: {sock.superhero_rating}",
                Div(
                    Form(method="get", action=f"/edit/{sock.id}", style="display: inline-block; margin-right: 10px;")(
                        Button("Edit", type="submit")
                    ),
                    Form(method="post", action=f"/delete/{sock.id}", style="display: inline-block;")(
                        Button("Delete", type="submit", onclick="return confirm('Are you sure you want to delete this sock?');")
                    )
                )
            ) for sock in sock_data
        ))
    except Exception as e:
        logger.error(f"Error fetching sock list: {e}")
        return P("Error fetching sock list. Please try again.")

# Routes
@rt('/')
def get():
    return Titled("Sock Tracker",
        P("Welcome to the Sock Tracker! Keep your socks organized."),
        A("Sock Care Tips", href="/care_tips"),
        H2("Add a new sock"),
        Div(sock_form(), id="sock-form"),
        H2("Your sock collection"),
        Div(sock_list(), id="sock-list")
    )

@rt('/add_sock')
def post(style: str, hue: str, size: str, mood: str, superhero_rating: int):
    logger.info(f"Received form data: style={style}, hue={hue}, size={size}, mood={mood}, superhero_rating={superhero_rating}")
    error = validate_sock_form(style, hue, size, mood, superhero_rating)
    if error:
        return Div(
            P(error, style="color: red;"),
            sock_form()
        )
    try:
        current_time = datetime.now().strftime("%Y-%m-%d")
        new_sock = Sock(sock_style=style, sock_hue=hue, foot_hugger_size=size, last_adventure=current_time, sock_mood=mood, superhero_rating=superhero_rating)
        logger.info(f"Attempting to insert new sock: {new_sock}")
        insert_result = socks.insert(new_sock)
        logger.info(f"Insert result: {insert_result}")
        if insert_result:
            return Div(
                P("Sock added successfully!", style="color: green;"),
                sock_list()
            )
        else:
            logger.error("Insert operation returned falsy value")
            return Div(
                P("Error adding sock. Please try again.", style="color: red;"),
                sock_form()
            )
    except Exception as e:
        logger.error(f"Error adding sock: {e}", exc_info=True)
        return Div(
            P(f"Error adding sock: {str(e)}", style="color: red;"),
            sock_form()
        )

@rt('/edit/{sock_id:int}')
def get(sock_id: int):
    try:
        sock = socks(id=sock_id)[0]
        return sock_form(sock)
    except IndexError:
        return P("Sock not found.")
    except Exception as e:
        logger.error(f"Error fetching sock for edit: {e}")
        return P("Error fetching sock. Please try again.")

@rt('/edit/{sock_id:int}')
def post(sock_id: int, style: str, hue: str, size: str, mood: str, superhero_rating: int):
    error = validate_sock_form(style, hue, size, mood, superhero_rating)
    if error:
        return Div(
            P(error, style="color: red;"),
            sock_form(socks(id=sock_id)[0])
        )
    try:
        current_time = datetime.now().strftime("%Y-%m-%d")
        socks.update({'sock_style': style, 'sock_hue': hue, 'foot_hugger_size': size, 'last_adventure': current_time, 'sock_mood': mood, 'superhero_rating': superhero_rating}, id=sock_id)
        return Div(
            P("Sock updated successfully!", style="color: green;"),
            sock_list()
        )
    except Exception as e:
        logger.error(f"Error updating sock: {e}")
        return Div(
            P("Error updating sock. Please try again.", style="color: red;"),
            sock_form(socks(id=sock_id)[0])
        )

@rt('/delete/{sock_id:int}')
def post(sock_id: int):
    try:
        socks.delete(id=sock_id)
        return sock_list()
    except Exception as e:
        logger.error(f"Error deleting sock: {e}")
        return P("Error deleting sock. Please try again.")

# Sock care tips
@rt('/care_tips')
def get():
    return Titled("Sock Care Tips",
        Ul(
            Li("Listen up, sock enthusiasts! Turn those bad boys inside out before washing. It's like giving them a suit of armor."),
            Li("Cold water and mild detergent are your friends. We're not trying to create sock-sized Hulks here."),
            Li("Bleach? That's a hard pass. It's like kryptonite for socks, and we're not in the business of creating sock villains."),
            Li("Air drying is the way to go. If you must use a dryer, keep it on low. We're not launching these socks into orbit."),
            Li("Sort your socks by color. It's not rocket science, but it'll prevent a civil war in your sock drawer."),
            Li("Upgrade your sock arsenal every 6-12 months. Even the best tech needs replacing sometimes.")
        ),
        A("Back to Sock Tracker", href="/")
    )

if __name__ == "__main__":
    serve()