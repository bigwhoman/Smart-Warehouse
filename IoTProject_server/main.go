package main

import (
	"IoTProject_server/API"
	"IoTProject_server/util"
	"fmt"
	"github.com/gorilla/mux"
	"net/http"
)

var running_port = "8080"

func main() {
	util.GenerateQRhexCode()
	fmt.Println("Starting server...")
	//til.Initializedatabase()
	handleRequests()
}
func handleRequests() {
	router := mux.NewRouter().StrictSlash(true)
	// router.HandleFunc("/signup", API.Signup)
	// router.HandleFunc("/login", API.Login)
	router.HandleFunc("/getqr", API.GetQRImage)
	http.ListenAndServe(":"+running_port, router)
}
