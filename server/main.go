package main

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/robfig/cron/v3"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"os"
	"os/exec"
	"time"
)

var db *gorm.DB

// TODO: These should always be in sync with what is in models.py
type Snap struct {
	SnapID              string    `json:"snap_id"`
	Title               string    `json:"title"`
	Name                string    `json:"name"`
	Version             string    `json:"version"`
	Summary             string    `json:"summary"`
	Description         string    `json:"description"`
	Icon                *string   `json:"icon"`
	Website             *string   `json:"website"`
	Contact             *string   `json:"contact"`
	Publisher           string    `json:"publisher"`
	Revision            int       `json:"revision"`
	Links               string    `json:"links"`
	Media               string    `json:"media"`
	DeveloperValidation string    `json:"developer_validation"`
	License             string    `json:"license"`
	LastUpdated         time.Time `json:"last_updated"`
	ActiveDevices       int       `json:"active_devices"`
	ReachesMinThreshold bool      `json:"reaches_min_threshold"`
}

type Score struct {
	SnapID          string  `json:"snap_id"`
	PopularityScore float64 `json:"popularity_score"`
	RecencyScore    float64 `json:"recency_score"`
	TrendingScore   float64 `json:"trending_score"`
}

func init() {
	var err error
	db, err = gorm.Open(sqlite.Open("../db.sqlite"), &gorm.Config{})
	if err != nil {
		fmt.Print(err)
		panic("failed to connect to the database")
	}
	db.AutoMigrate(&Snap{}, &Score{})
}

func getTopSnapsByField(orderField string) gin.HandlerFunc {
	return func(c *gin.Context) {
		var snaps []struct {
			SnapID string `json:"snap_id"`
			Name   string `json:"name"`
		}

		err := db.Table("scores").
			Select("snap.snap_id, snap.title, snap.name, snap.version, snap.publisher, snap.revision, scores." + orderField).
			Joins("INNER JOIN snap ON snap.snap_id = scores.snap_id").
			Order("scores." + orderField + " DESC").
			Limit(100).
			Find(&snaps).Error

		if err != nil {
			c.JSON(500, gin.H{"error": "Failed to fetch snaps"})
			return
		}

		c.JSON(200, snaps)
	}
}

func setupCron() {
	c := cron.New()
	c.AddFunc("@weekly", func() {
		fmt.Println("Updating scores")

		cmd := exec.Command("python3", "../collector/main.py")
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		err := cmd.Run()
		if err != nil {
			fmt.Println(err)
		}
	})

	c.Start()
}

func main() {
	setupCron()

	r := gin.Default()
	r.GET("/popular", getTopSnapsByField("popularity_score"))
	r.GET("/recent", getTopSnapsByField("recency_score"))
	r.GET("/trending", getTopSnapsByField("trending_score"))
	r.Run(":8080")

}
