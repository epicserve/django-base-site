export interface Category {
  id: number;
  name: string;
  category_type: "income" | "expense";
}

export interface TransactionLine {
  id?: number;
  category: number;
  category_name?: string;
  category_type?: "income" | "expense";
  amount: string;
  description: string;
}

export interface PaymentMethod {
  id: number;
  name: string;
  payment_type: "credit_card" | "debit_card" | "cash" | "bank_transfer" | "other";
  payment_type_display: string;
  last_four: string;
  is_active: boolean;
}

export interface Transaction {
  id: number;
  description: string;
  due_date: string;
  paid_date: string | null;
  is_paid: boolean;
  notes: string;
  recurring: number | null;
  payment_method: number | null;
  payment_method_name: string | null;
  lines: TransactionLine[];
  total_amount: string;
  transaction_type: "income" | "expense" | "";
  created_at: string;
}

export interface BudgetMember {
  id: number;
  user: number;
  email: string;
  name: string;
  role: "owner" | "member";
  gravatar_url: string;
  joined_at: string;
}

export interface Budget {
  id: number;
  members: BudgetMember[];
  created_at: string;
}

export interface CategoryBreakdown {
  category__name: string;
  total: string;
}

export interface DashboardData {
  income_total: string;
  expense_total: string;
  net_balance: string;
  income_by_category: CategoryBreakdown[];
  expense_by_category: CategoryBreakdown[];
  transactions: Transaction[];
  upcoming_transactions: Transaction[];
}

export interface RecurringTransaction {
  id: number;
  name: string;
  description: string;
  amount: string;
  category: number;
  category_name?: string;
  category_type?: "income" | "expense";
  frequency: string;
  interval: number;
  start_date: string;
  end_date: string | null;
  is_active: boolean;
  generated_through: string | null;
  next_due_date: string | null;
  created_at: string;
}

export interface CategoryBudget {
  id: number;
  category: number;
  month: string;
  assigned: string;
}

export interface BudgetOverviewCategory {
  id: number;
  name: string;
  category_type: "income" | "expense";
  assigned: string;
  activity: string;
  available: string;
}

export interface BudgetOverview {
  ready_to_assign: string;
  income_total: string;
  expense_assigned: string;
  categories: BudgetOverviewCategory[];
}

export interface ApiError {
  [key: string]: string[];
}
