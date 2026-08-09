# KAKA POS — Getting Started

*A short guide for the shop. Print this and keep it near the till.*

---

## 1. Opening the app

Double-click **`index.html`**. It opens in your browser and works without
internet.

Use **Chrome** or **Edge** if the computer has one — only those can save your
data straight to a file. On Windows 7 that means **Chrome 109**, the last
version Windows 7 accepts.

**Tip:** right-click it → *Send to → Desktop* to make a shortcut, or drag the
address into your browser's bookmarks bar so it is one click away every morning.

First time only, sign in with:

```
Username:  admin
Password:  admin123
```

A short setup guide appears. It asks for your shop name and currency, whether
you charge tax (**No** by default — the shelf price is what the customer pays),
where to keep your data, and a new admin password. **Take the two minutes** —
it also lets you clear the example products so you start with an empty shop.

---

## 2. Where your data is kept  ⚠️ important

During setup, choose **Create data file…** and save it somewhere you will
remember, for example:

```
Documents\KakaPOS\shop-data.json
```

From then on the app saves to that file **after every single sale**. Nothing
to press, nothing to remember.

**Check the coloured chip at the top right of the screen:**

| What you see | What it means |
|---|---|
| 💾 **Saved** (green) | Everything is being saved. All good. |
| 💾 **Browser only** (orange) | No file chosen — your data is only inside this browser. Fix it in **Users → Backup & Data**. |
| ⚠️ **Reconnect file** (red) | Click it, then click *Reconnect file*. Takes two seconds. |

**Once a week:** copy that `.json` file to a USB stick. That is your safety net
if the computer ever fails.

---

## 3. Selling — the basics

Open **Point of Sale**.

- **Scan** the barcode → the item lands in the basket. You can scan from
  **any screen**, even while you are typing in a search box — the app jumps to
  the till and adds it, and puts your search back the way it was. Your basket
  stays put while you look at other screens.
- **No barcode?** Type part of the name. Spelling mistakes and Arabic both work.
- **Item not in the system?** Just scan it — the app offers to add it. Type the
  name and how many you received, and it is created and added to the sale.
- **Selling a whole box?** Scan the barcode on the carton.
- **Loose items** (fruit, meat) — scan the label your scale prints.
- **Something with no barcode at all** — press **＋ Custom Item** and type a price.

When finished press **Charge**. Choose cash, card, transfer, mixed or customer
credit. For cash, tap the quick buttons (*Exact*, *50*, *100*…) and the change
is worked out for you.

**The receipt only prints if you ask for it** — press *Print Receipt* on the
confirmation. You can always reprint later from **Sales History**.

---

## 4. Fixing mistakes

Everything is recoverable. Go to **Sales History**:

- **↶ Undo** — cancels the whole sale and puts the stock back.
- **↩️ Refund** — gives back part of a sale.
- If the goods came back **damaged**, tick the box in the undo screen and they
  are recorded as a loss instead of going back on the shelf.

Nothing is ever silently deleted — cancelled sales stay in the list marked
*voided*, so your records stay honest.

---

## 5. The daily routine

**Morning**
1. Open the app, sign in.
2. **Cash Register → Open Register** — type the float you are starting with.

**During the day**
- Sell as normal. Check **Inventory → Alerts** for anything running low.

**Taking money out of the till** (or putting some in)

**Cash Register → Cash in & out**. Use it whenever money moves for a reason
that is not a sale:

| Reason | What it does |
|---|---|
| Owner withdrawal | Money out. **Not** an expense — it does not touch profit. |
| Supplier / restock paid in cash | Money out, and recorded as an expense. |
| Expense paid from the till | Money out, and recorded as an expense. |
| Money taken to the bank | Money out only. |
| Change / float added | Money in. |

Every movement is listed with who did it, and the drawer count at closing time
takes them into account. Made a mistake? Press 🗑 on the line and it is undone.

> If the goods were already entered as a **purchase order**, leave the "record
> as an expense" box unticked — otherwise the cost is counted twice.

**Evening**
1. **Cash Register → Close Register** — count the drawer and type the amount.
   The app shows any difference immediately.
2. Press **🖨 Print Z-Report** — one page with the day's sales, payment types,
   expenses, losses and profit. Keep it or file it.

---

## 6. Restocking

**Purchases → New Order** → choose the supplier → add the products → order by
**piece or box**. When the delivery arrives, press **Receive** and the stock
goes up automatically.

Need to hand the order to the supplier? Press **🖨** on the order line. It
prints on one A4 sheet with your shop details, theirs, what you want with case
sizes spelled out, the total, and space for both signatures.

**Low on things?** **Purchases → 🔄 Auto Reorder** shows everything below its
minimum, already grouped by supplier, with their phone number.

**Same item, new price?** Just receive it normally. Each delivery keeps the
price you paid for it, and the oldest stock is sold first — so the boxes you
bought cheaply stay cheap in your books until they run out. Your selling price
is separate: the same item can sell at one price whatever it cost you.

After receiving you are shown what the new price does to your margin, with a
suggested shelf price. Tick the ones you want, or leave prices alone.

To see what is on the shelf and at what price: open the product →
**💰 Wholesale → What this stock cost you**.

---

## 7. Staff accounts

**Users → + Add** creates an account for each person. Give cashiers the
**Cashier** role — they can sell and take payments, but cannot see your profit,
change prices or edit products.

Never share the admin password with staff.

---

## 8. If something goes wrong

The app is built to survive a bad day.

- **Power cut in the middle of a sale?** Reopen the app — it offers to bring
  the basket back exactly as it was.
- **Pressed Charge twice?** It only ever records one sale.
- **Someone imported the wrong file, or deleted things by mistake?**
  **Users → Backup & Data → Restore points** keeps an automatic copy from each
  of the last 7 days. Pick one and everything goes back.
- **Numbers look odd?** Same screen → **Data health → Run check**. It compares
  your stock against its own records and offers to repair anything that
  disagrees (a copy is saved first).
- **Walked away from the till?** The screen locks itself after 10 minutes and
  asks for your password. Change the delay in **Settings**.

---

## 9. The cash drawer

If the drawer is plugged into the receipt printer, it opens by itself on cash
payments. Nothing to set up — but if it does not, go to
**Paramètres → 💵 Tiroir-caisse** and press **Connecter le port de
l'imprimante** once. There is also an **Ouvrir le tiroir** button on the
**Caisse** screen for when you need it open without a sale.

---

## 10. Working in French

Press **FR** in the top bar. Everything changes — menus, buttons, messages,
tables, and the tickets and Z-report you print. Switch back with **EN** at any
time; it only changes what you see, never your data.

---

## 11. Scanner typing strange symbols?

If a scan comes out as `-&&&ààààà&ààà` instead of numbers, the scanner is
typing on a US keyboard while the computer is set to French or Arabic. **The
app understands it anyway** — items still ring up correctly.

To fix it properly, set the scanner to the same keyboard layout as the
computer; its manual has a barcode you scan once to do that.

**Settings → 🔎 Test the barcode scanner** shows exactly what the scanner sent
and what the app read, so you can check in five seconds.

---

## 12. Need a reminder?

Press the **❓** button at the top of the screen at any time — shortcuts and
short how-tos are built in.

**Keyboard:** `F2` search · `F4` payment · `Enter` confirm · `Esc` close.

---

## Two things to remember

1. **Keep the chip green.** If it turns orange or red, your sales are not being
   saved to your file.
2. **Copy the data file to a USB stick weekly.** It takes ten seconds and it is
   the only thing that protects you from a broken computer.

---

*The app runs entirely on this computer. No internet, no subscription, no
company can see your figures.*
