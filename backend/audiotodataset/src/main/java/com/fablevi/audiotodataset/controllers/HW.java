package com.fablevi.audiotodataset.controllers;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HW {
	@GetMapping("/")
	public String function () {
		return "hw";
	}
}
