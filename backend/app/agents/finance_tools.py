from typing import Optional, List, Dict, Any
import pandas as pd
from langchain_core.tools import tool
# pyrefly: ignore [missing-import]
from backend.app.services.pii_redactor import PIIRedactor

def _prepare_df(transactions: List[Dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(transactions)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    for col in ("category", "normalized_merchant", "raw_description"):
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("")
    return df

def build_finance_tools(transactions: List[Dict[str, Any]], goals: List[Dict[str, Any]]):
    """Returns LangChain tools bound (via closure) to ONE user's data.
    Every figure is computed exactly in pandas - the LLM never does arithmetic."""
    df = _prepare_df(transactions)
    def _filter(category, merchant, start_date, end_date):
        if df.empty:
            return df
        out = df
        if category:
            out = out[out["category"].str.lower() == category.strip().lower()]
        if merchant:
            out = out[out["normalized_merchant"].str.contains(merchant.strip(), case=False, na=False)]
        if start_date:
            out = out[out["date"] >= pd.to_datetime(start_date, errors="coerce")]
        if end_date:
            out = out[out["date"] <= pd.to_datetime(end_date, errors="coerce")]
        return out  
    
    @tool
    def sum_spending(category: Optional[str] = None, merchant: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """Total spending (Expenses only) matching the filters. category e.g. 'Dining';
        merchant is a name substring; dates are 'YYYY-MM-DD' inclusive. Omit filters for all-time."""
        sub = _filter(category, merchant, start_date, end_date)
        if sub.empty:
            return "No matching transactions found."
        exp = sub[sub["amount"]<0]
        return f"Total spending: Rs{float(-exp['amount'].sum()):,.2f} across {len(exp)} transaction(s)."

    @tool
    def sum_income(start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """Total INCOME (money received) in the optional 'YYYY-MM-DD' date range."""
        sub = _filter(None, None, start_date, end_date)
        if sub.empty:
            return "No matching transactions found."
        inc = sub[sub["amount"] > 0]
        return f"Total income: Rs{float(inc['amount'].sum()):,.2f} across {len(inc)} transaction(s)."

    @tool
    def count_transactions(category: Optional[str]=None, merchant:Optional[str]=None, start_date: Optional[str]=None, end_date:Optional[str]=None) -> str:
        """Count how many transactions match the filters. """
        return f"{len(_filter(category, merchant, start_date, end_date))} transaction(s) match"
        
    @tool
    def top_transactions(n: int = 5, kind: str = "expense", category: Optional[str] = None) -> str:
        """Largest transactions. kind='expense' (default) or 'income'. n = how many. category optional. """
        sub = _filter(category, None, None, None)
        if sub.empty:
            return "No matching transactions found."
        sub = sub[sub["amount"]<0] if kind == "expense" else sub[sub["amount"]>0]
        sub = sub.reindex(sub["amount"].abs().sort_values(ascending=False).index).head(max(1,n))
        return "\n".join(
            f"- {r['date'].date() if pd.notna(r['date']) else 'N/A'}: "
            f"{PIIRedactor.redact(str(r['normalized_merchant']))}"
            f" Rs{abs(float(r['amount'])):,.2f} ({r['category']})"
            for _,r in sub.iterrows()
        ) 
    
    @tool
    def category_breakdown(start_date: Optional[str]=None, end_date: Optional[str]=None) -> str:
        """Total spending grouped by category (optional date range)."""
        sub = _filter(None,None,start_date,end_date)
        exp = sub[sub["amount"]<0].copy() if not sub.empty else sub
        if exp.empty:
            return "No expenses found"
        exp["abs"] = exp["amount"].abs()
        grp = exp.groupby("category")["abs"].sum().sort_values(ascending=False)
        return "; ".join(f"{cat}: Rs{val:,.2f}" for cat, val in grp.items())

    @tool
    def list_goals() -> str:
        """List the user's financial goals with current vs target amounts."""
        if not goals:
            return "No goals set"
        return "; ".join(
            f"{g.get('goal_name')}: Rs{float(g.get('current_amount', 0)):,.0f} / Rs{float(g.get('target_amount', 0)):,.0f}"
            for g in goals
        )

    return [sum_spending, sum_income, count_transactions, top_transactions, category_breakdown, list_goals]

                        


            