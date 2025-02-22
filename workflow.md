```mermaid
flowchart TD
    subgraph Input["1️⃣ Data Collection"]
        direction LR
        Scopus["Scopus Database"]
        WoS["Web of Science"]
        Springer["Springer"]
    end

    subgraph Process["2️⃣ Document Processing"]
        direction TB
        Load["Initial Data Load"]
        DB1["Temporary Database"]
        subgraph Refine["Document Enrichment"]
            direction LR
            API1["Scopus API"]
            API2["CrossRef API"]
            Valid["Validation"]
        end
        DB2["Refined Document Database"]
    end

    subgraph Review["3️⃣ Document Review"]
        direction TB
        Sort["ASReview"]
        Clean["Final Document Set"]
    end

    subgraph Analysis["4️⃣ Analysis Pipeline"]
        direction LR
        Conv["Python → R"]
        Store["RDS Data"]
        R["Statistical Analysis"]
    end

    Input --> Load
    Load --> DB1
    DB1 --> API1
    API1 -->|Not Found| API2
    API1 & API2 -->|Success| Valid
    Valid --> DB2
    DB2 --> Sort
    Sort --> Clean
    Clean --> Conv
    Conv --> Store
    Store --> R
