```mermaid
flowchart LR
    A[Scopus] --> C{fa:fa-database SQL Database};
    B[Web of Science] --> C;
    C -- API --> D[Refine Scopus Database];
    D -- No Success --> E[Refine Crossref Database];
    D -- Success --> F{fa:fa-database Storage SQL DB};
    E -- Success --> F;
    F -- convert --> G{fa:fa-r-project Analysis with R};

    subgraph Data Acquisition
        A;
        B;
    end
    subgraph Database and Refinement
        C;
        D;
        E;
        F;
    end
    subgraph Analysis and Visualization
        G;
    end
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#f9f,stroke:#333,stroke-width:2px
    style C fill:#ccf,stroke:#333,stroke-width:2px
    style D fill:#ccf,stroke:#333,stroke-width:2px
    style E fill:#ccf,stroke:#333,stroke-width:2px
    style F fill:#ccf,stroke:#333,stroke-width:2px
    style G fill:#cfc,stroke:#333,stroke-width:2px
