import { Component } from "react";
import { BudgetApi } from "../api/client";
import type { BudgetOverview, BudgetOverviewCategory, Category, PaymentMethod, Transaction } from "../types";
import LoadingSpinner from "../components/LoadingSpinner";
import TransactionModal from "../components/TransactionModal";

interface Props {
  budgetPk: number;
  initialMonth?: string;
}

interface State {
  loading: boolean;
  error: string | null;
  overview: BudgetOverview | null;
  categories: Category[];
  paymentMethods: PaymentMethod[];
  month: string;
  editingAssigned: { [categoryId: number]: string };
  savingAssigned: { [categoryId: number]: boolean };
  showAddTransaction: boolean;
}

function getDefaultMonth(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

function prevMonth(month: string): string {
  const [year, mon] = month.split("-").map(Number);
  if (mon === 1) return `${year - 1}-12`;
  return `${year}-${String(mon - 1).padStart(2, "0")}`;
}

function nextMonth(month: string): string {
  const [year, mon] = month.split("-").map(Number);
  if (mon === 12) return `${year + 1}-01`;
  return `${year}-${String(mon + 1).padStart(2, "0")}`;
}

function formatMonth(month: string): string {
  const [year, mon] = month.split("-").map(Number);
  return new Date(year, mon - 1, 1).toLocaleString("default", { month: "long", year: "numeric" });
}

function fmt(val: string): string {
  const n = parseFloat(val);
  return `$${n.toFixed(2)}`;
}

class DashboardPage extends Component<Props, State> {
  private api: BudgetApi;

  constructor(props: Props) {
    super(props);
    this.api = new BudgetApi(props.budgetPk);
    const month = props.initialMonth ?? getDefaultMonth();
    this.state = {
      loading: true,
      error: null,
      overview: null,
      categories: [],
      paymentMethods: [],
      month,
      editingAssigned: {},
      savingAssigned: {},
      showAddTransaction: false,
    };
  }

  componentDidMount() {
    const params = new URLSearchParams(window.location.search);
    if (!params.get("month")) {
      window.history.replaceState(null, "", `?month=${this.state.month}`);
    }
    void this.loadData();
  }

  async loadData() {
    this.setState({ loading: true, error: null });
    try {
      const [overview, categories, paymentMethods] = await Promise.all([
        this.api.getBudgetOverview(this.state.month),
        this.api.getCategories(),
        BudgetApi.getPaymentMethods(),
      ]);
      this.setState({ overview, categories, paymentMethods, loading: false });
    } catch {
      this.setState({ loading: false, error: "Failed to load budget overview." });
    }
  }

  navigateMonth(month: string) {
    this.setState({ month, editingAssigned: {} }, () => { void this.loadData(); });
    window.history.replaceState(null, "", `?month=${month}`);
  }

  startEditAssigned(cat: BudgetOverviewCategory) {
    this.setState((s) => ({
      editingAssigned: { ...s.editingAssigned, [cat.id]: parseFloat(cat.assigned).toFixed(2) },
    }));
  }

  async saveAssigned(cat: BudgetOverviewCategory) {
    const { editingAssigned, month } = this.state;
    const val = editingAssigned[cat.id];
    if (val === undefined) return;
    this.setState((s) => ({ savingAssigned: { ...s.savingAssigned, [cat.id]: true } }));
    try {
      await this.api.upsertCategoryBudget(cat.id, month, val);
      const overview = await this.api.getBudgetOverview(month);
      this.setState((s) => {
        const ea = { ...s.editingAssigned };
        delete ea[cat.id];
        const sa = { ...s.savingAssigned };
        delete sa[cat.id];
        return { overview, editingAssigned: ea, savingAssigned: sa };
      });
    } catch {
      this.setState((s) => {
        const sa = { ...s.savingAssigned };
        delete sa[cat.id];
        return { savingAssigned: sa };
      });
    }
  }

  cancelEditAssigned(catId: number) {
    this.setState((s) => {
      const ea = { ...s.editingAssigned };
      delete ea[catId];
      return { editingAssigned: ea };
    });
  }

  renderHeader() {
    const { budgetPk } = this.props;
    const { month } = this.state;
    const isCurrentMonth = month === getDefaultMonth();
    return (
      <div className="d-flex align-items-center justify-content-between mb-4">
        <div className="d-flex align-items-center gap-3">
          <button
            className="btn btn-outline-secondary btn-sm"
            onClick={() => { this.navigateMonth(prevMonth(month)); }}
          >
            &laquo;
          </button>
          <h4 className="mb-0">{formatMonth(month)}</h4>
          <button
            className="btn btn-outline-secondary btn-sm"
            onClick={() => { this.navigateMonth(nextMonth(month)); }}
            disabled={isCurrentMonth}
          >
            &raquo;
          </button>
        </div>
        <div className="d-flex gap-2">
          <button
            className="btn btn-primary btn-sm"
            onClick={() => { this.setState({ showAddTransaction: true }); }}
          >
            + Transaction
          </button>
          <a className="btn btn-outline-secondary btn-sm" href={`/budgets/${budgetPk}/transactions/?month=${month}`}>
            All Transactions
          </a>
          <div className="dropdown">
            <button
              className="btn btn-outline-secondary btn-sm dropdown-toggle"
              type="button"
              data-bs-toggle="dropdown"
            >
              Manage
            </button>
            <ul className="dropdown-menu dropdown-menu-end">
              <li>
                <a className="dropdown-item" href={`/budgets/${budgetPk}/categories/`}>
                  Categories
                </a>
              </li>
              <li>
                <a className="dropdown-item" href={`/budgets/${budgetPk}/recurring/`}>
                  Recurring
                </a>
              </li>
              <li>
                <a className="dropdown-item" href={`/budgets/${budgetPk}/members/`}>
                  Members
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  renderReadyToAssign() {
    const { overview } = this.state;
    if (!overview) return null;
    if (parseFloat(overview.income_total) === 0) return null;
    const rta = parseFloat(overview.ready_to_assign);
    const isPositive = rta >= 0;
    return (
      <div className={`alert ${isPositive ? "alert-success" : "alert-danger"} d-flex justify-content-between align-items-center mb-4`}>
        <div>
          <strong>Ready to Assign</strong>
          <div className="small text-muted">
            Income {fmt(overview.income_total)} &minus; Assigned {fmt(overview.expense_assigned)}
          </div>
        </div>
        <span className="fs-4 fw-bold">{fmt(overview.ready_to_assign)}</span>
      </div>
    );
  }

  renderCategoryRow(cat: BudgetOverviewCategory) {
    const { editingAssigned, savingAssigned } = this.state;
    const isEditing = cat.id in editingAssigned;
    const isSaving = savingAssigned[cat.id];
    const available = parseFloat(cat.available);
    const isExpense = cat.category_type === "expense";

    const availableClass = isExpense
      ? available < 0
        ? "text-danger fw-bold"
        : available === 0
        ? "text-muted"
        : "text-success"
      : "text-success";

    return (
      <tr key={cat.id}>
        <td>{cat.name}</td>
        <td className="text-end">
          {isEditing ? (
            <div className="input-group input-group-sm justify-content-end" style={{ maxWidth: 130 }}>
              <span className="input-group-text">$</span>
              <input
                type="number"
                className="form-control"
                min="0"
                step="0.01"
                value={editingAssigned[cat.id]}
                autoFocus
                onChange={(e) => {
                  const v = e.target.value;
                  this.setState((s) => ({ editingAssigned: { ...s.editingAssigned, [cat.id]: v } }));
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") void this.saveAssigned(cat);
                  if (e.key === "Escape") this.cancelEditAssigned(cat.id);
                }}
                onBlur={() => { void this.saveAssigned(cat); }}
                disabled={isSaving}
              />
            </div>
          ) : (
            <span
              style={{ cursor: "pointer" }}
              title="Click to set target"
              onClick={() => { this.startEditAssigned(cat); }}
            >
              {parseFloat(cat.assigned) > 0 ? fmt(cat.assigned) : <span className="text-muted fst-italic">—</span>}
            </span>
          )}
        </td>
        <td className="text-end">{fmt(cat.activity)}</td>
        <td className={`text-end ${availableClass}`}>{fmt(cat.available)}</td>
      </tr>
    );
  }

  renderGrid() {
    const { overview } = this.state;
    if (!overview) return null;
    const income = overview.categories.filter((c) => c.category_type === "income");
    const expense = overview.categories.filter((c) => c.category_type === "expense");

    if (overview.categories.length === 0) {
      return (
        <div className="text-muted text-center py-5">
          No categories yet.{" "}
          <a href={`/budgets/${this.props.budgetPk}/categories/`}>Add some categories</a> to get started.
        </div>
      );
    }

    return (
      <div className="row g-3">
        {income.length > 0 && (
          <div className="col-md-6">
            <div className="card h-100">
              <div className="card-header bg-success bg-opacity-10 text-success small fw-bold">Income</div>
              <div className="table-responsive">
                <table className="table table-hover mb-0">
                  <thead className="table-light">
                    <tr>
                      <th>Category</th>
                      <th className="text-end">Activity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {income.map((cat) => (
                      <tr key={cat.id}>
                        <td>{cat.name}</td>
                        <td className="text-end text-success">{fmt(cat.activity)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
        {expense.length > 0 && (
          <div className="col-md-6">
            <div className="card h-100">
              <div className="card-header bg-danger bg-opacity-10 text-danger small fw-bold">Expenses</div>
              <div className="table-responsive">
                <table className="table table-hover mb-0">
                  <thead className="table-light">
                    <tr>
                      <th>Category</th>
                      <th className="text-end">Assigned</th>
                      <th className="text-end">Activity</th>
                      <th className="text-end">Available</th>
                    </tr>
                  </thead>
                  <tbody>
                    {expense.map((cat) => this.renderCategoryRow(cat))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  render() {
    const { loading, error, showAddTransaction, categories, paymentMethods } = this.state;

    return (
      <div>
        {this.renderHeader()}

        {loading && <LoadingSpinner />}
        {error && <div className="alert alert-danger">{error}</div>}

        {!loading && !error && (
          <>
            {this.renderReadyToAssign()}
            {this.renderGrid()}
          </>
        )}

        {showAddTransaction && (
          <>
            <div className="modal-backdrop fade show" onClick={() => { this.setState({ showAddTransaction: false }); }} />
            <TransactionModal
              categories={categories}
              paymentMethods={paymentMethods}
              budgetPk={this.props.budgetPk}
              transaction={null}
              onSave={async (data: Partial<Transaction>) => {
                await this.api.createTransaction(data);
                this.setState({ showAddTransaction: false });
                void this.loadData();
              }}
              onClose={() => { this.setState({ showAddTransaction: false }); }}
            />
          </>
        )}
      </div>
    );
  }
}

export default DashboardPage;
