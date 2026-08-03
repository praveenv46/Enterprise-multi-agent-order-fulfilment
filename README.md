# Enterprise Multi-Agent Order Fulfillment System

An enterprise-style **Agentic AI** system that automates customer quote generation, inventory validation, supplier delivery planning, and financial transaction processing using a team of specialized AI agents.

This project demonstrates how Large Language Models (LLMs) can coordinate business workflows through **multi-agent collaboration**, **tool calling**, and **SQL-backed enterprise data**.

---

## Overview

Modern enterprise workflows often require multiple business functions to work together before an order can be fulfilled. Instead of relying on a single AI assistant, this project uses a **multi-agent architecture** where each agent is responsible for a specific business capability.

The system processes customer orders by:

* Generating competitive quotes using historical pricing
* Validating inventory availability
* Estimating supplier delivery timelines
* Recording financial transactions
* Rejecting impossible orders with clear explanations

---

## Multi-Agent Architecture

The system consists of five specialized AI agents.

| Agent                  | Responsibility                                                                                          |
| ---------------------- | ------------------------------------------------------------------------------------------------------- |
| **Orchestrator Agent** | Coordinates the complete workflow and delegates tasks to worker agents                                  |
| **Sales Agent**        | Maps customer requests to catalog items, retrieves historical pricing, and generates competitive quotes |
| **Inventory Agent**    | Validates inventory availability and identifies shortages                                               |
| **Purchase Agent**     | Estimates supplier delivery dates and checks whether customer deadlines can be met                      |
| **Finance Agent**      | Validates cash availability, records transactions, and generates financial reports                      |

**Architecture Diagram**

                Customer
                    │
                    ▼
          Orchestrator Agent
     ┌────────┼─────────┬─────────┐
     ▼        ▼         ▼         ▼
 Sales     Inventory  Purchase  Finance
 Agent      Agent      Agent     Agent
     │        │         │         │
     └────────┴─────────┴─────────┘
                    │
                    ▼
          Quote / Order Decision

See **architecture.png** 

---

## Workflow

The order fulfilment workflow follows the sequence below:

1. Customer submits an order request.
2. Sales Agent generates a quote using historical pricing.
3. Inventory Agent validates stock availability.
4. If inventory is insufficient, the Purchase Agent estimates supplier delivery.
5. Finance Agent records stock-order and sales transactions when applicable.
6. The Orchestrator returns either:

   * Approved quotation
   * Delivery information
   * Transaction IDs
   * Rejection reason

For the complete workflow diagram, see **workflow.md**.

---

## Technologies

* Python
* SmolAgents
* OpenAI GPT-4o-mini
* SQLite
* SQLAlchemy
* Pandas
* Multi-Agent AI
* Tool Calling
* Prompt Engineering

---

## Key Features

* Multi-Agent AI architecture
* Tool-calling workflow
* Historical quote analysis
* Automated inventory validation
* Supplier lead-time estimation
* Financial transaction processing
* SQL database integration
* Explainable order approval and rejection
* End-to-end automated testing

---

## Repository Structure

```text
.
├── project_starter.py
├── README.md
├── workflow.md
├── architecture.png
├── quote_requests.csv
├── quote_requests_sample.csv
├── quotes.csv
├── test_results.csv
├── requirements.txt
└── LICENSE
```

---

## Example Output

### Successful Order

```text
Quoted Amount: $65.00

Fulfillment Decision:
Order Fulfilled

Transaction IDs:
20
21
22
```

### Rejected Order

```text
Order rejected because the supplier cannot meet the requested delivery date.
```

---

## Testing

The system was evaluated using a dataset of simulated customer requests.

The evaluation demonstrates:

* Successful quote generation
* Inventory validation
* Supplier delivery planning
* Financial transaction recording
* Automatic rejection of infeasible customer requests

Evaluation results are available in:

```text
test_results.csv
```

---

## Future Improvements

* Semantic product matching using vector embeddings for more robust product identification.
* Multi-supplier optimization based on cost and delivery performance.
* Dynamic pricing using demand and inventory levels.
* Parallel processing for large multi-item orders.
* ERP integration with platforms such as SAP or Microsoft Dynamics.

---

## Skills Demonstrated

* Agentic AI
* Multi-Agent Systems
* LLM Tool Calling
* Prompt Engineering
* Enterprise Workflow Automation
* SQL Database Integration
* Business Process Automation
* Python Application Development

---

## License

This project is available under the MIT License.
