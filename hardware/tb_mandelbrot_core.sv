module tb_mandelbrot_core;

  localparam int MAX_ITER = 120;

  // 100 MHz clock
  logic clk = 0;
  always #5 clk = ~clk;

  logic rst_n;

  logic start;
  logic signed [31:0] c_re_q28, c_im_q28;
  logic busy, done;
  logic [15:0] iter_count;

  int err_count = 0;

  // DUT (Q4.28 version)
  mandelbrot_core #(.MAX_ITER(MAX_ITER)) dut (
    .clk(clk), .rst_n(rst_n),
    .start(start),
    .c_re_q28(c_re_q28),
    .c_im_q28(c_im_q28),
    .busy(busy),
    .done(done),
    .iter_count(iter_count)
  );

  // Convert real -> Q4.28 signed
  function automatic signed [31:0] q28(real x);
    q28 = $rtoi(x * (1<<28));
  endfunction

  // Run a single point and check iteration range
  task automatic run_point(
      input string name,
      input real re,
      input real im,
      input int exp_min,
      input int exp_max
  );
    int timeout_cycles;
    begin
      // Load c in Q4.28
      c_re_q28 = q28(re);
      c_im_q28 = q28(im);

      $display("\n=== %s ===", name);
      $display("c=(%f,%f)  c_re_q28=0x%08h  c_im_q28=0x%08h",
               re, im, c_re_q28, c_im_q28);

      // Pulse start for 1 clock
      start = 1'b1;
      @(posedge clk);
      start = 1'b0;

      // Wait for done with a timeout
      timeout_cycles = 0;
      while (!done && timeout_cycles < (MAX_ITER + 50)) begin
        @(posedge clk);
        timeout_cycles++;
      end

      if (!done) begin
        $display("FAIL %s: TIMEOUT waiting for done", name);
        err_count++;
      end else begin
        $display("%s: iter=%0d (busy=%0b)", name, iter_count, busy);

        if (!(iter_count >= exp_min && iter_count <= exp_max)) begin
          $display("FAIL %s: iter=%0d not in [%0d,%0d]",
                   name, iter_count, exp_min, exp_max);
          err_count++;
        end else begin
          $display("OK   %s", name);
        end
      end

      // Let DUT return to IDLE (FINISH waits for !start)
      @(posedge clk);
    end
  endtask

  initial begin
    // init
    rst_n = 0;
    start = 0;
    c_re_q28 = '0;
    c_im_q28 = '0;

    // reset for a few cycles
    repeat(5) @(posedge clk);
    rst_n = 1;

    // Inside set: should hit MAX_ITER (or MAX_ITER exactly)
    run_point("C0", 0.0, 0.0, MAX_ITER-1, MAX_ITER);

    // Outside set: should escape quickly
    run_point("C1p5", 1.5, 0.0, 0, 10);

    // Typically bounded
    run_point("C-1", -1.0, 0.0, MAX_ITER-1, MAX_ITER);

    // Near boundary: wide acceptable range
    run_point("Cboundary", -0.75, 0.1, 5, MAX_ITER);

    // Final status
    if (err_count == 0)
      $display("\n*** tb_mandelbrot_core PASS ***");
    else
      $display("\n*** tb_mandelbrot_core FAIL: %0d error(s) ***", err_count);

    $finish;
  end

endmodule