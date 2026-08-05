# KAKA POS — Getting Started

*A short guide for the shop. Print this and keep it near the till.*

---

## 1. Opening the app

Double-click **`index.html`**. It opens in your browser and works without
internet.

**Tip:** right-click it → *Send to → Desktop* to make a shortcut, or drag the
address into your browser's bookmarks bar so it is one click away every morning.

First time only, sign in with:

```
Username:  admin
Password:  admin123
```

A short setup guide appears. It asks for your shop name, currency and tax,
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

- **Scan** the barcode → the item lands in the basket.
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

**Low on things?** **Purchases → 🔄 Auto Reorder** shows everything below its
minimum, already grouped by supplier, with their phone number.

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

## 9. Need a reminder?

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
