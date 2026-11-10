# Feast Fast — merged project

Run:  `python main.py`   (Python 3.10+, tkinter; Pillow optional for profile photos)

Manager login: `manager` / `Manager@123`

## How everything connects
main.py (App + PAGES map + shared design system + auth)
 ├─ Public:   landing → customer_login / create_account / manager_login
 ├─ Customer (all use CustomerPage sidebar from dashboard.py)
 │    dashboard · menu_page (+ veg_page, non_veg_page, beverage_page)
 │    cart_page → payment_page (payment + payment_done) → orders_page · check_availability (reservation) → my_booking · profile_page
 └─ Manager (all use AdminPage sidebar from admin_reservation.py)
      admin_dashboard · admin_menu · admin_orders · admin_reservation

Shared data modules: menu_data.py (menu), orders_store.py (orders), check_availability.BOOKINGS (tables),
db.py (SQLite file feastfast.db, created on first run), with orders_store.py, reservations_store.py,
menu_data.py and notifications.py as the small modules that read/write it.

## Database (SQLite)
`feastfast.db` is created automatically the first time you run `python main.py`
(tables: users, menu_items, orders, order_items, payments, tables, reservations, notifications).
An older feastfast.db is upgraded automatically (the new `payments` table is added; old orders keep working).
If an old `users.json` / `data/*.json` exists, it is imported once, then left alone.

## Payment
- Cart → **Proceed to Payment** → pay by **QR** or **Account transfer** → type the **journal number** → Submit.
  The order is only created at this point, so a customer who hasn't paid can't order.
- The manager gets a notification with the journal number and amount. In **Manage Order** they check the
  canteen's bank statement, then press **Confirm payment**. **Start Preparing** only works after that
  (enforced in SQL, not just hidden).
- **Wrong journal number?**
  - Format is checked (6-20 letters/digits, no `123456` / `000000` style numbers).
  - One journal number can be used for **one order only** (database unique index), so a single real
    payment can't be reused for many orders.
  - Manager presses **Wrong journal no.** → the customer is notified and can use **Fix payment** in My Order
    (3 tries per order in total, `MAX_ATTEMPTS`), after that they must call the manager.
- Settings (manager phone number, account details, journal length, tries) are at the top of `orders_store.py`.
  **Put the real manager number in `MANAGER_PHONE`** — it is shown on the About Us page and in the refund messages.
- To show the real QR code, save it as `canteen_qr.png` next to `payment_page.py` (otherwise a placeholder is drawn).

## Rules
- Customer can cancel an order only while it is **Pending**. Once the manager clicks *Start Preparing* it is locked.
- If a **paid** order is cancelled while Pending, the payment becomes **Refund due**. The customer phones the manager
  (number on About Us); the manager sends the money back by hand and presses **Mark Refunded**.
- Admin is notified (🔔 + pop-up) when a paid order arrives, when a new journal number is entered, and when a customer cancels.
- Customer is notified when the payment is confirmed, when preparing starts, when the order is **Ready**,
  when a journal number can't be found, and when a refund is sent.
- To try it: run `python main.py` in two terminals (one customer, one manager). Each window checks the database every 2 s.

## Profile (customer)
- Edit first name, last name, phone, email and photo, then **Save changes**.
- Changing the email asks for your password; orders, bookings and notifications move to the new email.
- **Change password** needs the current password; the new one must be strong, confirmed and different. Other devices are signed out.
- **Log out everywhere** and **Delete account** (asks for the password) are in the Danger zone.
