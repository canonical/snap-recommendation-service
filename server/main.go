package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"

	_ "github.com/lib/pq"
	_ "github.com/mattn/go-sqlite3"
)

type Config struct {
	Driver  string
	ConnStr string
}

type Item struct {
	ID   string `json:"id"`
	Name string `json:"name"`
}

type DatabaseHandler struct {
	DB *sql.DB
}

func NewDatabaseHandler(config Config) (*DatabaseHandler, error) {
	db, err := sql.Open(config.Driver, config.ConnStr)
	if err != nil {
		return nil, err
	}

	if err = db.Ping(); err != nil {
		return nil, err
	}
	return &DatabaseHandler{DB: db}, nil
}

func (dh *DatabaseHandler) GetItems() ([]Item, error) {
	rows, err := dh.DB.Query("SELECT snap_id, name FROM snap")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var items []Item
	for rows.Next() {
		var item Item
		if err := rows.Scan(&item.ID, &item.Name); err != nil {
			return nil, err
		}
		items = append(items, item)
	}
	return items, nil
}

func main() {

	config := Config{
		Driver:  "sqlite3",
		ConnStr: "../db.sqlite",
	}

	dbHandler, err := NewDatabaseHandler(config)
	if err != nil {
		log.Fatalf("Failed to initialize database: %v", err)
	}
	defer dbHandler.DB.Close()

	http.HandleFunc("/items", func(w http.ResponseWriter, r *http.Request) {
		items, err := dbHandler.GetItems()
		if err != nil {

			log.Printf("Failed to retrieve items: %v", err)
			http.Error(w, "Failed to retrieve items", http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(items)
	})

	port := 8080
	log.Printf("Server running on port %d...", port)
	log.Fatal(http.ListenAndServe(fmt.Sprintf(":%d", port), nil))
}
