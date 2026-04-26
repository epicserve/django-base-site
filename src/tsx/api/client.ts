import type {
  Budget,
  BudgetMember,
  BudgetOverview,
  Category,
  CategoryBudget,
  DashboardData,
  PaymentMethod,
  RecurringTransaction,
  Transaction,
} from "../types";

function getCsrfToken(): string {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : "";
}

async function request<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-CSRFToken": getCsrfToken(),
    ...(options.headers as Record<string, string>),
  };

  const response = await fetch(url, { ...options, headers });

  if (!response.ok) {
    let errorData: unknown;
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: response.statusText };
    }
    throw errorData;
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export class BudgetApi {
  private readonly base: string;

  constructor(budgetPk: number) {
    this.base = `/api/budgets/${budgetPk}`;
  }

  // Dashboard
  getDashboard(month?: string): Promise<DashboardData> {
    const params = month ? `?month=${month}` : "";
    return request<DashboardData>(`${this.base}/dashboard/${params}`);
  }

  getBudget(): Promise<Budget> {
    return request<Budget>(`${this.base}/`);
  }

  // Categories
  getCategories(): Promise<Category[]> {
    return request<Category[]>(`${this.base}/categories/`);
  }

  createCategory(data: Omit<Category, "id">): Promise<Category> {
    return request<Category>(`${this.base}/categories/`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  updateCategory(pk: number, data: Partial<Category>): Promise<Category> {
    return request<Category>(`${this.base}/categories/${pk}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  deleteCategory(pk: number): Promise<void> {
    return request<void>(`${this.base}/categories/${pk}/`, {
      method: "DELETE",
    });
  }

  // Transactions
  getTransactions(params?: { month?: string; type?: string }): Promise<Transaction[]> {
    const qs = new URLSearchParams();
    if (params?.month) qs.set("month", params.month);
    if (params?.type) qs.set("type", params.type);
    const query = qs.toString() ? `?${qs.toString()}` : "";
    return request<Transaction[]>(`${this.base}/transactions/${query}`);
  }

  createTransaction(data: Partial<Transaction>): Promise<Transaction> {
    return request<Transaction>(`${this.base}/transactions/`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  updateTransaction(pk: number, data: Partial<Transaction>): Promise<Transaction> {
    return request<Transaction>(`${this.base}/transactions/${pk}/`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  deleteTransaction(pk: number): Promise<void> {
    return request<void>(`${this.base}/transactions/${pk}/`, {
      method: "DELETE",
    });
  }

  markTransactionPaid(pk: number): Promise<Transaction> {
    return request<Transaction>(`${this.base}/transactions/${pk}/mark-paid/`, {
      method: "POST",
    });
  }

  // Recurring Transactions
  getRecurring(): Promise<RecurringTransaction[]> {
    return request<RecurringTransaction[]>(`${this.base}/recurring/`);
  }

  createRecurring(data: Partial<RecurringTransaction>): Promise<RecurringTransaction> {
    return request<RecurringTransaction>(`${this.base}/recurring/`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  updateRecurring(pk: number, data: Partial<RecurringTransaction>): Promise<RecurringTransaction> {
    return request<RecurringTransaction>(`${this.base}/recurring/${pk}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  deleteRecurring(pk: number, deleteFutureUnpaid?: boolean): Promise<void> {
    const query = deleteFutureUnpaid ? "?delete_future_unpaid=1" : "";
    return request<void>(`${this.base}/recurring/${pk}/${query}`, {
      method: "DELETE",
    });
  }

  // Budget Overview
  getBudgetOverview(month?: string): Promise<BudgetOverview> {
    const params = month ? `?month=${month}` : "";
    return request<BudgetOverview>(`${this.base}/overview/${params}`);
  }

  upsertCategoryBudget(categoryPk: number, month: string, assigned: string): Promise<CategoryBudget> {
    return request<CategoryBudget>(`${this.base}/category-budgets/${categoryPk}/`, {
      method: "PUT",
      body: JSON.stringify({ month, assigned }),
    });
  }

  // Payment Methods (user-scoped, no budget context)
  static getPaymentMethods(): Promise<PaymentMethod[]> {
    return request<PaymentMethod[]>("/api/payment-methods/");
  }

  static createPaymentMethod(data: Omit<PaymentMethod, "id" | "payment_type_display">): Promise<PaymentMethod> {
    return request<PaymentMethod>("/api/payment-methods/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  static updatePaymentMethod(pk: number, data: Partial<PaymentMethod>): Promise<PaymentMethod> {
    return request<PaymentMethod>(`/api/payment-methods/${pk}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  static deletePaymentMethod(pk: number): Promise<void> {
    return request<void>(`/api/payment-methods/${pk}/`, {
      method: "DELETE",
    });
  }

  // Members
  getMembers(): Promise<BudgetMember[]> {
    return request<BudgetMember[]>(`${this.base}/members/`);
  }

  inviteMember(email: string, role: string): Promise<BudgetMember> {
    return request<BudgetMember>(`${this.base}/members/`, {
      method: "POST",
      body: JSON.stringify({ email, role }),
    });
  }

  removeMember(pk: number): Promise<void> {
    return request<void>(`${this.base}/members/${pk}/`, {
      method: "DELETE",
    });
  }
}
