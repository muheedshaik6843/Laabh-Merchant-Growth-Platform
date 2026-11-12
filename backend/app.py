import os, random, math, json
from datetime import datetime, timedelta, date, timezone
from functools import wraps
from flask import Flask, jsonify, request, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, '.env'))
app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'laabh-local-demo-change-me')
db_url = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'laabh.db'))
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
db = SQLAlchemy(app)
def utc_now(): return datetime.now(timezone.utc).replace(tzinfo=None)
DEMO_EMAILS={'demo@laabh.in','cafe@laabh.in','pharmacy@laabh.in'}

class Merchant(db.Model):
    id=db.Column(db.Integer, primary_key=True); name=db.Column(db.String(100), nullable=False); category=db.Column(db.String(40)); city=db.Column(db.String(60)); email=db.Column(db.String(120), unique=True); password=db.Column(db.String(255)); created_at=db.Column(db.DateTime, default=utc_now)
class Product(db.Model):
    id=db.Column(db.Integer, primary_key=True); merchant_id=db.Column(db.Integer, db.ForeignKey('merchant.id'), index=True); name=db.Column(db.String(100)); category=db.Column(db.String(50)); price=db.Column(db.Float); cost=db.Column(db.Float); stock=db.Column(db.Integer); reorder_level=db.Column(db.Integer)
class Customer(db.Model):
    id=db.Column(db.Integer, primary_key=True); merchant_id=db.Column(db.Integer, db.ForeignKey('merchant.id'), index=True); name=db.Column(db.String(100)); phone=db.Column(db.String(20)); segment=db.Column(db.String(30)); joined_at=db.Column(db.DateTime)
class Sale(db.Model):
    id=db.Column(db.Integer, primary_key=True); merchant_id=db.Column(db.Integer, db.ForeignKey('merchant.id'), index=True); customer_id=db.Column(db.Integer, db.ForeignKey('customer.id'), index=True); created_at=db.Column(db.DateTime, index=True); total=db.Column(db.Float); profit=db.Column(db.Float)
class SaleItem(db.Model):
    id=db.Column(db.Integer, primary_key=True); sale_id=db.Column(db.Integer, db.ForeignKey('sale.id'), index=True); product_id=db.Column(db.Integer, db.ForeignKey('product.id')); quantity=db.Column(db.Integer); unit_price=db.Column(db.Float); unit_cost=db.Column(db.Float)
class Campaign(db.Model):
    id=db.Column(db.Integer, primary_key=True); merchant_id=db.Column(db.Integer, db.ForeignKey('merchant.id'), index=True); name=db.Column(db.String(120)); segment=db.Column(db.String(30)); discount_pct=db.Column(db.Float); status=db.Column(db.String(30)); incremental_profit=db.Column(db.Float); created_at=db.Column(db.DateTime, default=utc_now); simulated=db.Column(db.Boolean, default=True)
class OfferEvaluation(db.Model):
    id=db.Column(db.Integer, primary_key=True); merchant_id=db.Column(db.Integer, db.ForeignKey('merchant.id')); created_at=db.Column(db.DateTime, default=utc_now); payload=db.Column(db.Text); result=db.Column(db.Text)

@app.cli.command('seed')
def seed_command():
    seed_data(True)

def seed_data(force=False):
    with app.app_context():
        if Merchant.query.first() and not force: return
        if force: db.drop_all()
        db.create_all(); rng=random.Random(42)
        profiles=[('Anand Kirana','Kirana','Hyderabad'),('Brew & Bean Café','Cafe','Hyderabad'),('Sree Lakshmi Pharmacy','Pharmacy','Secunderabad')]
        catalog={
          'Kirana':['Basmati Rice','Toor Dal','Sunflower Oil','Masala Chai','Atta 5kg','Sugar','Milk 1L','Biscuits','Detergent','Bath Soap','Coffee Powder','Noodles','Ghee','Chips','Eggs','Bread','Yogurt','Spices','Juice','Cereal','Pickle','Flour','Lentils','Dishwash Liquid','Shampoo','Toothpaste','Water Bottle','Chocolate','Peanuts','Coconut'],
          'Cafe':['Cold Coffee','Cappuccino','Masala Chai','Filter Coffee','Veg Sandwich','Paneer Wrap','Brownie','Blueberry Muffin','Croissant','Iced Latte','Lemon Tea','Pasta','Cheesecake','Espresso','Mocha','Bagel','Cookies','Fries','Smoothie','Club Sandwich','Tea Cake','Donut','Garlic Bread','Salad','Hot Chocolate','Affogato','Cold Brew','Quiche','Pancakes','Mango Shake'],
          'Pharmacy':['Paracetamol','Vitamin C','ORS Sachet','Cough Syrup','Antacid','Bandage','Sanitizer','Pain Relief Gel','Thermometer','Multivitamin','Allergy Tablets','Calcium Tabs','Face Mask','Digital BP Monitor','First Aid Kit','Eye Drops','Cough Lozenges','Protein Powder','Baby Lotion','Diabetic Strips','Zinc Tablets','Hand Wash','Nasal Spray','Antiseptic Cream','Iron Tablets','Sunscreen','Mosquito Repellent','Digestive Enzyme','Cotton Roll','Band-Aid']}
        for mi,(name,cat,city) in enumerate(profiles):
            m=Merchant(name=name,category=cat,city=city,email=['demo@laabh.in','cafe@laabh.in','pharmacy@laabh.in'][mi],password=generate_password_hash('laabh123')); db.session.add(m); db.session.flush()
            products=[]
            for i,pname in enumerate(catalog[cat]):
                margin=[.20,.38,.32][mi]; price=round(rng.uniform(35,480),2); cost=round(price*(1-margin-rng.uniform(0,.08)),2)
                p=Product(merchant_id=m.id,name=pname,category=['Essentials','Beverages','Food','Personal Care','Health'][i%5],price=price,cost=cost,stock=rng.randint(5,90),reorder_level=18); db.session.add(p); products.append(p)
            db.session.flush(); customers=[]
            for i in range(120):
                segment=['Loyal','Active','At Risk','Lapsed','New'][i%5]
                c=Customer(merchant_id=m.id,name=f'{["Aarav","Meera","Ravi","Ananya","Kiran","Sana","Vikram","Priya"][i%8]} { ["Reddy","Shah","Kumar","Rao","Patel","Singh"][i%6]} {i+1}',phone=f'+91 98{mi}{i:07d}',segment=segment,joined_at=utc_now()-timedelta(days=rng.randint(30,600))); db.session.add(c); customers.append(c)
            db.session.flush()
            for day in range(90):
                when=utc_now().replace(hour=0,minute=0,second=0,microsecond=0)-timedelta(days=89-day)
                count=rng.randint(12,28)
                for _ in range(count):
                    c=rng.choice(customers); p=rng.choice(products); qty=rng.choices([1,2,3],[.72,.23,.05])[0]; total=round(p.price*qty,2); prof=round((p.price-p.cost)*qty,2)
                    hour=rng.choices(range(8,22),weights=[1,1,2,2,3,4,5,5,5,4,5,5,4,3])[0]
                    sale=Sale(merchant_id=m.id,customer_id=c.id,created_at=when+timedelta(hours=hour,minutes=rng.randint(0,59)),total=total,profit=prof); db.session.add(sale); db.session.flush(); db.session.add(SaleItem(sale_id=sale.id,product_id=p.id,quantity=qty,unit_price=p.price,unit_cost=p.cost))
        db.session.commit()

def current_merchant():
    mid=session.get('merchant_id')
    return db.session.get(Merchant,mid) if mid else None
def auth_required(fn):
    @wraps(fn)
    def wrapped(*a,**kw):
        if not current_merchant(): return jsonify({'error':'Please log in'}),401
        return fn(*a,**kw)
    return wrapped
def merchant_id(): return current_merchant().id
def fmt_money(n): return round(float(n or 0),2)

@app.get('/api/health')
def health(): return jsonify({'ok':True,'simulated':True})
@app.post('/api/login')
def login():
    data=request.get_json(silent=True) or {}; m=Merchant.query.filter_by(email=data.get('email','').strip().lower()).first()
    if m and check_password_hash(m.password,data.get('password','')): session['merchant_id']=m.id; return jsonify({'merchant':{'id':m.id,'name':m.name,'category':m.category,'city':m.city}})
    return jsonify({'error':'Email or password is incorrect'}),401
@app.post('/api/register')
def register():
    data=request.get_json(silent=True) or {}; name=str(data.get('name','')).strip(); email=str(data.get('email','')).strip().lower(); password=str(data.get('password','')); category=str(data.get('category','Kirana')).strip(); city=str(data.get('city','')).strip()
    safe_label=lambda value: all(ch.isalnum() or ch.isspace() or ch in ".,'&-()" for ch in value)
    if len(name)<2 or not safe_label(name) or not safe_label(city) or '@' not in email or len(password)<8 or category not in ('Kirana','Cafe','Pharmacy','Retail','Other'):
        return jsonify({'error':'Enter a name, valid email, password with at least 8 characters, business type, and city.'}),400
    if Merchant.query.filter_by(email=email).first(): return jsonify({'error':'An account with this email already exists.'}),409
    m=Merchant(name=name,category=category,city=city or 'India',email=email,password=generate_password_hash(password)); db.session.add(m); db.session.commit(); session['merchant_id']=m.id
    return jsonify({'merchant':{'id':m.id,'name':m.name,'category':m.category,'city':m.city}}),201
@app.post('/api/logout')
def logout(): session.clear(); return jsonify({'ok':True})
@app.get('/api/me')
def me():
    m=current_merchant()
    return (jsonify({'merchant':{'id':m.id,'name':m.name,'category':m.category,'city':m.city}}) if m else (jsonify({'error':'Please log in'}),401))
@app.get('/api/merchants')
@auth_required
def merchants():
    m=current_merchant(); available=Merchant.query.all() if m.email in DEMO_EMAILS else [m]
    return jsonify([{'id':item.id,'name':item.name,'category':item.category} for item in available])
@app.post('/api/switch-merchant')
@auth_required
def switch_merchant():
    data=request.get_json(silent=True) or {}; m=db.session.get(Merchant,data.get('id'))
    if not m:return jsonify({'error':'Merchant not found'}),404
    current=current_merchant()
    if current.email not in DEMO_EMAILS and current.id!=m.id:return jsonify({'error':'You can only access your own merchant account.'}),403
    session['merchant_id']=m.id; return jsonify({'merchant':{'id':m.id,'name':m.name,'category':m.category,'city':m.city}})
@app.get('/api/dashboard')
@auth_required
def dashboard():
    mid=merchant_id(); sales=Sale.query.filter_by(merchant_id=mid).all(); today=date.today(); day_sales=[s for s in sales if s.created_at.date()==today]
    recent=[s for s in sales if s.created_at>=utc_now()-timedelta(days=30)]; customers=Customer.query.filter_by(merchant_id=mid).all(); distinct={s.customer_id for s in recent}; returning=sum(1 for c in customers if sum(1 for s in recent if s.customer_id==c.id)>1)
    daily=[]
    for i in range(13,-1,-1):
        d=today-timedelta(days=i); ss=[s for s in sales if s.created_at.date()==d]; daily.append({'date':d.strftime('%b %d'),'revenue':round(sum(s.total for s in ss),2),'profit':round(sum(s.profit for s in ss),2)})
    weekly=[]
    for i in range(5,-1,-1):
        end=utc_now()-timedelta(days=i*7); start=end-timedelta(days=7); ss=[s for s in sales if start<=s.created_at<end]; weekly.append({'week':f'W{i+1}','revenue':round(sum(s.total for s in ss),2),'profit':round(sum(s.profit for s in ss),2)})
    byproduct=db.session.query(Product.name,db.func.sum(Sale.total)).join(SaleItem,SaleItem.product_id==Product.id).join(Sale,Sale.id==SaleItem.sale_id).filter(Sale.merchant_id==mid).group_by(Product.name).all()
    top=sorted([{'name':k,'revenue':round(v or 0,2)} for k,v in byproduct],key=lambda x:-x['revenue'])[:5]
    rev=sum(s.total for s in day_sales); profit=sum(s.profit for s in day_sales)
    return jsonify({'merchant':{'id':current_merchant().id,'name':current_merchant().name,'category':current_merchant().category,'city':current_merchant().city},'kpis':{'todayRevenue':round(rev,2),'todayProfit':round(profit,2),'transactions':len(day_sales),'activeCustomers':len(distinct),'returningCustomers':returning,'aov':round(sum(s.total for s in recent)/len(recent),2) if recent else 0},'daily':daily,'weekly':weekly,'topProducts':top,'customerCount':len(customers),'simulated':True})
@app.get('/api/products')
@auth_required
def products():
    mid=merchant_id(); products=Product.query.filter_by(merchant_id=mid).all(); result=[]
    for p in products:
        count=sum((i.quantity or 0) for i in SaleItem.query.filter_by(product_id=p.id).all()); result.append({'id':p.id,'name':p.name,'category':p.category,'price':p.price,'cost':p.cost,'margin':round((p.price-p.cost)/p.price*100,1),'stock':p.stock,'reorderLevel':p.reorder_level,'units90d':count,'velocity':round(count/90,1),'status':'Low stock' if p.stock<=p.reorder_level else ('Fast moving' if count>100 else 'Healthy')})
    return jsonify(sorted(result,key=lambda x:(x['stock']>x['reorderLevel'],-x['units90d'])))
@app.get('/api/customers')
@auth_required
def customers_api():
    mid=merchant_id(); seg=request.args.get('segment'); query=Customer.query.filter_by(merchant_id=mid)
    if seg and seg!='All segments': query=query.filter_by(segment=seg)
    rows=[]
    for c in query.limit(180):
        ss=Sale.query.filter_by(customer_id=c.id).all(); total=sum(s.total for s in ss); last=max([s.created_at for s in ss],default=c.joined_at)
        rows.append({'id':c.id,'name':c.name,'phone':c.phone,'segment':c.segment,'visits':len(ss),'spend':round(total,2),'aov':round(total/len(ss),2) if ss else 0,'lastVisit':last.strftime('%b %d, %Y'),'lapseScore':min(98,15+max(0,(utc_now()-last).days)*2)})
    return jsonify(rows)
@app.get('/api/recommendations')
@auth_required
def recommendations():
    mid=merchant_id(); rows=[]
    sales=Sale.query.filter_by(merchant_id=mid).all()
    revenue=sum(s.total for s in sales); gross_profit=sum(s.profit for s in sales)
    avg_order=revenue/len(sales) if sales else 0
    margin=gross_profit/revenue if revenue else 0
    audience=Customer.query.filter(Customer.merchant_id==mid,Customer.segment.in_(['At Risk','Lapsed'])).count()
    # Transparent scenario assumptions: 25% campaign response, 5% baseline buying,
    # a 5% offer, and ₹80 setup cost. Merchants must still run Profit Guard.
    offer_redemptions=math.ceil(audience*.25); baseline_orders=math.ceil(audience*.05)
    incremental_orders=max(0,offer_redemptions-baseline_orders)
    discount=avg_order*.05; discounted_unit_profit=avg_order*margin-discount
    winback_profit=incremental_orders*discounted_unit_profit-baseline_orders*discount-80
    rows.append({'title':'Bring regulars back this week','description':f'Planning scenario from {audience} at-risk or lapsed customers: assumes 25% response, 5% baseline buying, a 5% offer, and ₹80 setup cost. Validate the offer in Profit Guard before launch.','revenue':round(offer_redemptions*max(0,avg_order-discount)),'profit':round(winback_profit),'priority':'High' if winback_profit>0 else 'Medium','action':'Create a win-back campaign' if winback_profit>0 else 'Review with Profit Guard','icon':'users'})
    product_rows=Product.query.filter_by(merchant_id=mid).all(); product_stats=[]
    for p in product_rows:
        items=SaleItem.query.filter_by(product_id=p.id).all(); units=sum(i.quantity or 0 for i in items); velocity=units/90
        if p.stock<=p.reorder_level:
            target_stock=max(p.reorder_level*2,math.ceil(velocity*14))
            forecast_units=max(1,target_stock-p.stock)
            title='Restock '+p.name
            description=f'Suggest ordering {forecast_units} units toward a 14-day target of {target_stock}, based on {units} units sold in the seeded 90-day history. Revenue and profit assume those units sell through.'
        else:
            forecast_units=math.ceil(velocity*7*.10)
            title='Feature '+p.name+' this week'
            description=f'Illustrative 10% unit lift over the recent weekly sales pace, based on {units} units sold in the seeded 90-day history.'
        product_stats.append({'title':title,'description':description,'revenue':round(forecast_units*p.price),'profit':round(forecast_units*(p.price-p.cost)),'priority':'Medium','action':'Review inventory','icon':'box','units':units,'stock':p.stock,'reorder':p.reorder_level})
    product_stats.sort(key=lambda r:(r['stock']>r['reorder'],-r['units']))
    rows.extend(product_stats[:2])
    return jsonify(rows[:3])
@app.post('/api/profit-guard')
@auth_required
def profit_guard():
    d=request.get_json(silent=True) or {}
    try:
        price=float(d.get('price')); cost=float(d.get('cost')); discount=float(d.get('discountPct')); audience=max(0,int(d.get('audience',100))); visits=max(0,int(d.get('incrementalSales',20))); conversion=max(0,min(1,float(d.get('conversion',.25)))); campaign=max(0,float(d.get('campaignCost',250))); cannibalization=max(0,min(1,float(d.get('cannibalizationPct',.25))))
        if price<=0 or cost<0 or cost>=price or discount<0 or discount>=100: raise ValueError()
    except (ValueError,TypeError): return jsonify({'error':'Enter valid values. Price must exceed cost and discount must be under 100%.'}),400
    gross=price-cost; amt=price*discount/100; unit=price-amt-cost; discounted=int(audience*conversion); extra=min(visits,max(0,int(discounted*(1-cannibalization)))); baseline=max(0,discounted-extra); cannibal=baseline*amt; campaign_profit=extra*unit-campaign-cannibal; break_even=math.ceil((campaign+cannibal)/unit) if unit>0 else 10**9; approved=campaign_profit>0
    out={'approved':approved,'originalProfit':round(gross,2),'discountAmount':round(amt,2),'discountedProfit':round(unit,2),'incrementalSales':extra,'baselineDiscountedSales':baseline,'cannibalizationCost':round(cannibal,2),'campaignCost':round(campaign,2),'incrementalProfit':round(campaign_profit,2),'totalCampaignRevenue':round((extra+baseline)*(price-amt),2),'breakEvenSales':break_even,'risk':'High' if discount>=30 or cannibalization>=.5 else 'Moderate' if discount>=15 else 'Low','recommendation':'Approve this targeted offer.' if approved else 'Reject this offer or narrow the audience, reduce the discount, or lower campaign cost.'}
    ev=OfferEvaluation(merchant_id=merchant_id(),payload=json.dumps(d),result=json.dumps(out)); db.session.add(ev); db.session.flush(); out['id']=ev.id; ev.result=json.dumps(out); db.session.commit(); return jsonify(out)
@app.post('/api/campaigns')
@auth_required
def create_campaign():
    d=request.get_json(silent=True) or {}; name=str(d.get('name','Profit Guard campaign')).strip()[:120]
    safe_label=lambda value: all(ch.isalnum() or ch.isspace() or ch in ".,'&-()%" for ch in value)
    if not name or not safe_label(name): return jsonify({'error':'Campaign name contains unsupported characters.'}),400
    evaluation=OfferEvaluation.query.filter_by(id=d.get('evaluationId'),merchant_id=merchant_id()).first()
    if not evaluation: return jsonify({'error':'Run Profit Guard again before confirming this campaign.'}),400
    result=json.loads(evaluation.result); payload=json.loads(evaluation.payload)
    if not result.get('approved'): return jsonify({'error':'Only Profit Guard approved campaigns can be simulated.'}),400
    seg=str(payload.get('segment','At Risk'))
    if seg not in ('At Risk','Loyal','Active','New','All customers'): seg='At Risk'
    c=Campaign(merchant_id=merchant_id(),name=name,segment=seg,discount_pct=float(payload.get('discountPct',0)),status='Simulated',incremental_profit=float(result.get('incrementalProfit',0)),simulated=True); db.session.add(c); db.session.commit(); return jsonify({'id':c.id,'message':'Campaign delivery simulated. No messages were sent.','campaign':name})
@app.get('/api/campaigns')
@auth_required
def campaigns():
    return jsonify([{'id':c.id,'name':c.name,'segment':c.segment,'discountPct':c.discount_pct,'status':c.status,'incrementalProfit':c.incremental_profit,'date':c.created_at.strftime('%b %d, %Y'),'simulated':True,'reached':random.Random(c.id).randint(20,100),'holdout':random.Random(c.id+1).randint(12,60),'redemption':random.Random(c.id+2).randint(8,35)} for c in Campaign.query.filter_by(merchant_id=merchant_id()).order_by(Campaign.created_at.desc()).all()])
@app.get('/api/forecast')
@auth_required
def forecast():
    mid=merchant_id(); sales=Sale.query.filter_by(merchant_id=mid).all(); daily={}
    for s in sales: daily.setdefault(s.created_at.date(),[]).append(s.total)
    values=[sum(daily.get(date.today()-timedelta(days=i),[])) for i in range(1,29)]; avg=sum(values)/max(1,len(values)); series=[]
    for i in range(7): series.append({'date':(date.today()+timedelta(days=i+1)).strftime('%a'),'actual':None,'forecast':round(avg*(1+(i-3)*.008),2),'low':round(avg*.82,2),'high':round(avg*1.18,2)})
    return jsonify({'series':series,'weeklyRevenue':round(avg*7,2),'monthlyRevenue':round(avg*30,2),'volume':round(len(sales)/90*7),'confidence':'Medium','method':'28-day historical daily average; illustrative estimate'})
@app.post('/api/assistant')
@auth_required
def assistant():
    q=(request.get_json(silent=True) or {}).get('question','').strip().lower(); sales=Sale.query.filter_by(merchant_id=merchant_id()).all(); customers=Customer.query.filter_by(merchant_id=merchant_id()).all()
    today=[s for s in sales if s.created_at.date()==date.today()]; rev=sum(s.total for s in today); profit=sum(s.profit for s in today)
    if any(w in q for w in ['profit','munafa','లాభం']): answer=f"Today’s estimated profit is ₹{profit:,.0f} from ₹{rev:,.0f} in revenue. These figures use simulated demo transactions."
    elif any(w in q for w in ['customer','visiting','stopped','ग्राहक','కస్టమర్']): answer=f"There are {len(customers)} customers in your demo profile. Your customer list includes at-risk and lapsed segments you can review for a targeted win-back test."
    elif any(w in q for w in ['product','item','highest','ఉత్పత్తి']):
        p=Product.query.filter_by(merchant_id=merchant_id()).order_by(Product.price-Product.cost).first(); answer=f"{p.name} currently has the highest unit margin at ₹{p.price-p.cost:.0f} per sale in the demo catalog."
    else: answer=f"Your demo shop recorded ₹{rev:,.0f} revenue and ₹{profit:,.0f} profit today. Try asking about profit, customers, or your best product."
    return jsonify({'answer':answer,'language':'auto','simulated':True})
@app.get('/')
def index(): return send_from_directory(app.static_folder,'index.html')
@app.get('/<path:path>')
def assets(path): return send_from_directory(app.static_folder,path)

with app.app_context():
    db.create_all()
    if not Merchant.query.first(): seed_data()

if __name__=='__main__': app.run(host='127.0.0.1',port=int(os.getenv('PORT',5000)),debug=os.getenv('FLASK_DEBUG')=='1')
